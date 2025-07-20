import os
import sys
import asyncio
import time
import numpy as np

from openai import OpenAI, AsyncOpenAI

from pyht.async_client import AsyncClient
from pyht.client import TTSOptions
from pyht.protos import api_pb2
import simpleaudio as sa

from common_utils import maybe_start_alternative_narrator, generate_new_line, get_camera, encode_image, capture, cut_to_n_words
import audio_feedback

MAX_TOKENS = int(os.environ.get("MAX_TOKENS"))

AUDIO_GENERATION_SAMPLE_RATE=22050
MAX_MINUTES_PER_AUDIO=4

'''Async LLM HANDLING'''
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
        max_tokens=MAX_TOKENS
    )
    
    response_text = response.choices[0].message.content
    return response_text

''' TTS '''
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

'''MAIN'''
async def async_main(from_error=False, text=None, debug_camera=False):
    print("☕ Waking David up... (instant narrator)")

    reader = get_camera('<video0>')
    # Wait for the camera to initialize and adjust light levels
    #time.sleep(2)

    capture(reader, debugging=debug_camera) # loop until camera shows something
    # When debugging the camera, the above command loops in infinite
    if not from_error:
        print("👋 Hello!")
        audio_feedback.startup()

    # OpenAI client initialization
    client = AsyncOpenAI()

    # PlayHT API client initialization
    clientPlayHT = AsyncClient(os.environ.get("PLAYHT_USER_ID"),os.environ.get("PLAYHT_API_KEY"))
    options = playht_options()

    max_times = int(os.environ.get("MAX_TIMES"))
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
            text = await analyze_image_async(base64_image, client, script=script)
        
        try:
            text = cut_to_n_words(text, int(MAX_TOKENS*5/4))
            print("🎙️ David says:")
            print(text)
            await async_play_audio(clientPlayHT.tts(text, voice_engine="PlayHT2.0-turbo", options=options))

        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break
        
        script = script + [{"role": "assistant", "content": text}]
        
        print("😝 David is pausing...")
        await asyncio.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Turning off 
    if not tts_error_occurred:
        audio_feedback.turnoff()

    await asyncio.get_running_loop().run_in_executor(None, reader.close) # Turn off the camera
    await clientPlayHT.close()

    if tts_error_occurred:
        maybe_start_alternative_narrator(tts_error, from_error, text, "./narrator.py")
    else:
        print(f"Reached the maximum of {max_times}... turning off the narrator.")
    sys.exit(0)
    
if __name__ == "__main__":    
    from script_arguments import make_arguments
    args = make_arguments(parser_description="InstantNarrator")

    asyncio.run(async_main(**vars(args)))
