import os
import asyncio

import numpy as np
from openai import OpenAI
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

AUDIO_GENERATION_SAMPLE_RATE=22050  # Assuming a sample rate of 22050 Hz

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

async def async_play_audio(data):
    buff_size = 10485760
    ptr = 0
    start_time = time.time()
    buffer = np.empty(buff_size, np.float16)
    audio = None
    i = -1
    async for chunk in data:
        i += 1
        if i == 0:
            start_time = time.time()
            continue  # Drop the first response, we don't want a header.
        elif i == 1:
            print("First audio byte received in:", time.time() - start_time)
        for sample in np.frombuffer(chunk, np.float16):
            buffer[ptr] = sample
            ptr += 1
        if i == 5:
            # Give a 4 sample worth of breathing room before starting
            # playback
            audio = sa.play_buffer(buffer, 1, 2, AUDIO_GENERATION_SAMPLE_RATE)
    approx_run_time = ptr / 24_000
    await asyncio.sleep(max(approx_run_time - time.time() + start_time, 0))
    if audio is not None:
        audio.stop()


def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except IOError as e:
        if e.errno != errno.EACCES:
            raise
        time.sleep(0.1)  # File is still being written, wait a bit and retry


'''LLM handling'''
def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": os.environ.get("NEW_IMAGE_PROMPT")},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base34,{base64_image}",
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
        + generate_new_line(base64_image),
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
        + generate_new_line(base64_image),
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

def playht_options():
    # Set the speech options
    return TTSOptions(
        
        voice=os.environ.get("PLAYHT_VOICE_ID"),
        
        # you can pass any value between 8000 and 48000, 24000 is default
        sample_rate=AUDIO_GENERATION_SAMPLE_RATE,
        
        # the generated audio encoding, supports 'raw' | 'mp3' | 'wav' | 'ogg' | 'flac' | 'mulaw'
        format=api_pb2.FORMAT_WAV,
        
        speed=0.9)

'''MAIN'''
async def async_main():
    reader = imageio.get_reader('<video0>')
    # Wait for the camera to initialize and adjust light levels
    time.sleep(2)

    # OpenAI client initialization
    clientOpenAI = OpenAI()

    # PlayHT API client initialization
    client = AsyncClient(os.environ.get("PLAYHT_USER_ID"),os.environ.get("PLAYHT_API_KEY"))
    options = playht_options()

    script = []
    while True:
        
        print("👀 David is watching...")
        base64_image = capture(reader)

        print("🧠 David is thinking...")
        text = await analyze_image_async(base64_image, clientOpenAI, script)
        
        print("🎙️ David says:")
        print(text)
        await async_play_audio(client.tts(text, voice_engine="PlayHT2.0-turbo", options=options))
        
        script = script + [{"role": "assistant", "content": text}]
        
        await asyncio.sleep(3)  # Wait a bit before sending a new image

    # Cleanup.
    await client.close()    
    
if __name__ == "__main__":
    asyncio.run(async_main())
