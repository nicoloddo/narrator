import os
import subprocess
import asyncio

import numpy as np
from openai import OpenAI, AsyncOpenAI
import base64
import time
import simpleaudio as sa
import errno
from pyht.async_client import AsyncClient
from pyht.client import TTSOptions
from pyht.protos import api_pb2

import imageio
import io
from PIL import Image

AUDIO_GENERATION_SAMPLE_RATE=22050
MAX_MINUTES_PER_AUDIO=4

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)


'''Common tools'''
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except IOError as e:
        if e.errno != errno.EACCES:
            raise
        time.sleep(0.1)  # File is still being written, wait a bit and retry

'''Capture picture'''
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

'''LLM handling'''
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

def analyze_image(base64_image, clientOpenAI, script):    
    response = clientOpenAI.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": os.environ.get("AGENT_PROMPT"),
            },
        ]
        + script
        + generate_new_line(base64_image, len(script)==0),
        max_tokens=300,
    )
    
    response_text = response.choices[0].message.content
    return response_text

async def analyze_image_async(base64_image, clientOpenAI, script):    
    response = await clientOpenAI.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": os.environ.get("AGENT_PROMPT"),
            },
        ]
        + script
        + generate_new_line(base64_image, len(script)==0),
        max_tokens=300,
    )
    
    response_text = response.choices[0].message.content
    return response_text

'''Text to speech'''
def calculate_buffer_size(duration_minutes, sample_rate, data_type):
    max_duration_seconds = duration_minutes * 60  # Convert minutes to seconds
    bytes_per_sample = np.dtype(data_type).itemsize
    return max_duration_seconds * sample_rate * bytes_per_sample

async def async_play_audio(data):
    max_minutes_per_audio = MAX_MINUTES_PER_AUDIO
    audio_sample_dtype = np.float16

    buff_size = calculate_buffer_size(max_minutes_per_audio, AUDIO_GENERATION_SAMPLE_RATE, audio_sample_dtype)
    ptr = 0
    start_time = time.time()
    buffer = np.empty(buff_size, audio_sample_dtype)
    audio = None
    i = -1
    async for chunk in data:
        i += 1
        if i == 0:
            start_time = time.time()
            continue  # Drop the first response, we don't want a header.
        elif i == 1:
            print("First audio byte received in:", time.time() - start_time)
        for sample in np.frombuffer(chunk, audio_sample_dtype):
            buffer[ptr] = sample
            ptr += 1
        if i == 5:
            # Give a 4 sample worth of breathing room before starting
            # playback
            audio = sa.play_buffer(buffer, 1, 2, AUDIO_GENERATION_SAMPLE_RATE)
    approx_run_time = ptr / AUDIO_GENERATION_SAMPLE_RATE *(11/10) # Add a 1/10 of it to be sure it finishes
    await asyncio.sleep(max(approx_run_time + (start_time - time.time()), 0))
    if audio is not None:
        audio.stop()

def playht_options():
    # Set the speech options
    return TTSOptions(
        
        voice=os.environ.get("PLAYHT_VOICE_ID"),
        
        # you can pass any value between 8000 and 48000, 24000 is default
        sample_rate=AUDIO_GENERATION_SAMPLE_RATE,
        
        # the generated audio encoding, supports 'raw' | 'mp3' | 'wav' | 'ogg' | 'flac' | 'mulaw'
        format=api_pb2.FORMAT_WAV,
        
        speed=0.9)

def maybe_start_alternative_narrator(e, from_error, text):
    if from_error: # If this script was run from an error of another narrator, we stop it here to not create loops of runs.
        print(f"Error occurred: {e}\n This was the alternative narrator..\n\n")
        raise e
    else: # We start the alternative narrator.
        print(f"Rate Limit error occurred: {e}\nStarting the alternative narrator.\n\n")
        command = [
            "python", "./narrator.py",
            "--from-error",
            "--text", text
        ]
        subprocess.run(command)

'''MAIN'''
async def async_main(from_error=False, text=None):
    print("☕ Waking David up...")

    reader = imageio.get_reader('<video0>')
    # Wait for the camera to initialize and adjust light levels
    time.sleep(2)

    # OpenAI client initialization
    clientOpenAI = AsyncOpenAI()

    # PlayHT API client initialization
    client = AsyncClient(os.environ.get("PLAYHT_USER_ID"),os.environ.get("PLAYHT_API_KEY"))
    options = playht_options()

    max_times = os.environ.get("MAX_TIMES")
    count = 0

    # TTS error handling
    tts_error_occurred = False
    tts_error = None

    script = []
    while count != max_times:
        
        if from_error and count == 0 and text is not None:
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
            await async_play_audio(client.tts(text, voice_engine="PlayHT2.0-turbo", options=options))
        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break
        
        script = script + [{"role": "assistant", "content": text}]
        
        print("😝 David is pausing...")
        await asyncio.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Turning off 
    await asyncio.get_running_loop().run_in_executor(None, reader.close) # Turn off the camera
    await client.close()

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
        help="Text to say. Required if --from-error is True."
    )

    args = parser.parse_args()

    # Conditional requirement check
    if args.from_error and not args.text:
        parser.error("--text is required when --from-error is specified.")

    asyncio.run(async_main(**vars(args)))
