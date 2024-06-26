import os
import sys
import base64
import time

from openai import OpenAI

from elevenlabs import generate, play, set_api_key, voices, RateLimitError

from common_utils import maybe_start_alternative_narrator, generate_new_line, get_camera, encode_image, capture, cut_to_n_words
import audio_feedback

MAX_TOKENS = int(os.environ.get("MAX_TOKENS"))

''' LLM HANDLING '''
def analyze_image(base64_image, client, script):
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
        max_tokens=MAX_TOKENS
    )
    response_text = response.choices[0].message.content
    return response_text

''' TTS '''
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

''' MAIN '''
def main(from_error=False, text=None, debug_camera=False):
    print("☕ Waking David up... (narrator)")

    time.sleep(2) # Wait for camera
    reader = get_camera('<video0>')
    #time.sleep(2) # Wait for the camera to initialize and adjust light levels

    capture(reader, debugging=debug_camera) # loop until camera shows something
    # When debugging the camera, the above command loops in infinite
    if not from_error:
        print("👋 Hello!")
        audio_feedback.startup()

    # OpenAI client initialization
    client = OpenAI()

    # ElevenLabs API initialization
    set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

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
            text = analyze_image(base64_image, client, script=script)

        try:
            text = cut_to_n_words(text, int(MAX_TOKENS*5/4))
            print("🎙️ David says:")
            print(text)
            play_audio(text)

        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break

        script = script + [{"role": "assistant", "content": text}]

        print("😝 David is pausing...")
        time.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Turning off
    if not tts_error_occurred:
        audio_feedback.turnoff()

    reader.close() # Turn off the camera

    if tts_error_occurred:
        maybe_start_alternative_narrator(tts_error, from_error, text, "./instant_narrator.py")
    else:
        print(f"Reached the maximum of {max_times}... turning off the narrator.")
    sys.exit(0)

if __name__ == "__main__":
    from script_arguments import make_arguments
    args = make_arguments(parser_description="Narrator")

    main(**vars(args))
