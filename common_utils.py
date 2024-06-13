import subprocess

import os

import base64
import errno
import time
from PIL import Image
import io
import numpy as np

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

def capture(reader, frames_dir):
    frame = reader.get_next_data()
        
    # Convert the frame to a PIL image
    pil_img = Image.fromarray(frame)

    # Resize the image
    max_size = 500
    ratio = max_size / max(pil_img.size)
    new_size = tuple([int(x*ratio) for x in pil_img.size])
    resized_img = pil_img.resize(new_size, Image.LANCZOS)

    # Save the frame as an image file for debugging purposes
    path = os.path.join(frames_dir, "frame.jpg")
    resized_img.save(path)

    # Convert PIL image to a bytes buffer and encode in base64
    buffered = io.BytesIO()
    resized_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_str

def check_if_dark(image):
    # Convert the image to grayscale
    gray_image = image.convert('L')
    # Convert the grayscale image to a numpy array
    image_array = np.array(gray_image)
    # Calculate the average pixel intensity
    average_intensity = image_array.mean()

    # Define a threshold for darkness (you may need to adjust this based on your specific needs)
    darkness_threshold = 50  # A common value; lower means darker

    # Return True if the image is dark, False otherwise
    return average_intensity < darkness_threshold