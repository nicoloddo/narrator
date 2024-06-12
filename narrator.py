import os
import sys
import subprocess
from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, set_api_key, voices, RateLimitError

import imageio
import io
from PIL import Image

client = OpenAI()

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

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


def play_audio(text):
    audio = generate(
        text,
        voice=os.environ.get("ELEVENLABS_VOICE_ID"),
        model="eleven_turbo_v2")

    unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    play(audio)

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


def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": os.environ.get("AGENT_PROMPT"),
            },
        ]
        + script
        + generate_new_line(base64_image, len(script)==0), # If the script is empty this is the starting image
        max_tokens=300,
    )
    response_text = response.choices[0].message.content
    return response_text


def capture(reader):
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

def maybe_start_alternative_narrator(e, from_error, text):
    if from_error: # If this script was run from an error of another narrator, we stop it here to not create loops of runs.
        print(f"Error occurred: {e}\n This was the alternative narrator..\n\n")
        raise e
    else: # We start the alternative narrator.
        print(f"Rate Limit error occurred: {e}\nStarting the alternative narrator..\n\n")
        command = [
            "python", "./instant_narrator.py",
            "--from-error",
            "--text", text
        ]
        subprocess.run(command)

def main(from_error=False, text=None):
    print("☕ Waking David up...")

    reader = imageio.get_reader('<video0>')
    # Wait for the camera to initialize and adjust light levels
    time.sleep(2)

    max_times = os.environ.get("MAX_TIMES")
    count = 0

    # TTS error handling
    tts_error_occurred = False
    tts_error = None

    script = []
    while count != max_times:

        if count == 0 and text is not None:
            text = text
        else:
            # analyze posture
            print("👀 David is watching...")
            base64_image = capture(reader)

            print("🧠 David is thinking...")
            text = analyze_image(base64_image, script=script)

        try:
            print("🎙️ David says:")
            print(text)
            play_audio(text)

        except RateLimitError as e:
            tts_error_occurred = True
            tts_error = e
            break

        script = script + [{"role": "assistant", "content": text}]

        print("😝 David is pausing...")
        time.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Turning off
    reader.close() # Turn off the camera

    if tts_error_occurred:
        maybe_start_alternative_narrator(tts_error, from_error, text)
    else:
        print(f"Reached the maximum of {max_times}... turning off the narrator.")
    sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="InstantNarrator")

    # Boolean switch argument
    parser.add_argument(
        "--from-error",
        action="store_true",
        help="If the script was run from an error of another narrator. It stores the Boolean value True if the specified argument is present in the command line and False otherwise."
    )

    # Argument that is conditionally required
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text to say at first instance of speech. Required if --from-error is True."
    )

    args = parser.parse_args()

    # Conditional requirement check
    if args.from_error and not args.text:
        parser.error("--text is required when --from-error is specified.")

    main(**vars(args))
