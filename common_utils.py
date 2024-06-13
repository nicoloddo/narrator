import subprocess

import os

import base64
import errno
import time
from PIL import Image
import io
import numpy as np

import audio_feedback

# Create the frames folder if it doesn't exist
FRAMES_DIR = os.path.join(os.getcwd(), "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)

''' **************************************************************************************************** '''
''' ERROR HANDLING UTILS '''
def maybe_start_alternative_narrator(e, from_error, text, alternative_narrator="./instant_narrator.py"):
    if from_error: # If this script was run from an error of another narrator, we stop it here to not create loops of runs.
        print(f"Error occurred: {e}\nThis was the alternative narrator..\n\n")
        raise e
    else: # We start the alternative narrator.
        print(f"Error occurred: {e}\nStarting the alternative narrator.\n\n")
        command = [
            "python", alternative_narrator,
            "--from-error",
            "--text", text
        ]
        subprocess.run(command)

''' **************************************************************************************************** '''
''' LLM UTILS '''
def generate_new_line(base64_image, first_prompt_bool):
    if first_prompt_bool:
        prompt = os.environ.get("FIRST_IMAGE_PROMPT")
    else:
        prompt = os.environ.get("NEW_IMAGE_PROMPT")

    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{base64_image}",
                        "detail": "high"
                    }
                },
            ],
        },
    ]


''' **************************************************************************************************** '''
''' IMAGE CAPTURING UTILS '''
PRINT_DEBUG_EACH_N_FRAMES = 50
DARKNESS_THRESHOLD = int(os.environ.get("DARKNESS_THRESHOLD"))
SATURATION_UNIFORMITY_THRESHOLD = int(os.environ.get("SATURATION_UNIFORMITY_THRESHOLD"))
HUE_UNIFORMITY_THRESHOLD = int(os.environ.get("HUE_UNIFORMITY_THRESHOLD"))

def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)

def capture(reader, frames_dir=FRAMES_DIR, *, debugging=False):
    if debugging:
        print("Started camera debugging")

    is_dark_or_uniform = True

    count_frames = 0
    while is_dark_or_uniform or debugging:

        frame = reader.get_next_data()
            
        # Convert the frame to a PIL image
        pil_img = Image.fromarray(frame)

        # Resize the image
        max_size = 500
        ratio = max_size / max(pil_img.size)
        new_size = tuple([int(x*ratio) for x in pil_img.size])
        resized_img = pil_img.resize(new_size, Image.LANCZOS)

        # Convert PIL image to a bytes buffer and encode in base64
        buffered = io.BytesIO()
        resized_img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        is_dark_or_uniform = check_image_quality(resized_img, count_frames, debugging)

        if debugging and count_frames % PRINT_DEBUG_EACH_N_FRAMES == 0:
            if is_dark_or_uniform:
                print("I can't see...")
                audio_feedback.cant_see()
            else:
                print("I can see clear!")
                audio_feedback.i_see()
            print()

        # Count frames for debugging prints    
        count_frames += 1
        if count_frames == PRINT_DEBUG_EACH_N_FRAMES + 1:
            count_frames = 0

    # We are out of the loop, so the image is ok:
    # Save the frame as an image file for debugging purposes
    path = os.path.join(frames_dir, "frame.jpg")
    resized_img.save(path)
    return img_str

def check_image_quality(image,  count_frames, debugging=False):
    # Convert to grayscale and check brightness
    gray_image = image.convert('L')
    average_intensity = np.array(gray_image).mean()

    # Convert to HSV and check color uniformity
    hsv_image = image.convert('HSV')
    hsv_array = np.array(hsv_image)

    hue_std = hsv_array[:,:,0].std()  # Standard deviation of the hue channel
    #sat_std = hsv_array[:,:,1].std()  # Standard deviation of the saturation channel

    darkness_threshold = DARKNESS_THRESHOLD
    #sat_uniformity_threshold = SATURATION_UNIFORMITY_THRESHOLD  # Adjust this threshold based on your needs
    hue_uniformity_threshold = HUE_UNIFORMITY_THRESHOLD  # Adjust this threshold based on your needs

    if debugging and count_frames % PRINT_DEBUG_EACH_N_FRAMES == 0:
        print(f"Hue std: {hue_std}")
        #print(f"Sat std: {sat_std}")
        print(f"Brightness intensity: {average_intensity}")

    # Determine if the image is dark or lacks color variance
    is_dark = average_intensity < darkness_threshold
    #lacks_color_variance = hue_std < hue_uniformity_threshold and sat_std < sat_uniformity_threshold
    #lacks_color_variance = sat_std < sat_uniformity_threshold
    lacks_color_variance = hue_std < hue_uniformity_threshold

    return is_dark or lacks_color_variance