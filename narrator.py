import os
import sys
import base64
import time
import json

from openai import OpenAI

from elevenlabs import generate, play, set_api_key, voices, RateLimitError
from elevenlabs import Voice, VoiceSettings

from environment_selector import env
from common_utils import (
    maybe_start_alternative_narrator,
    get_camera,
    encode_image,
    capture,
    cut_to_n_words,
    count_tokens,
)
import audio_feedback
import db_parser as db

MAX_TOKENS = int(env.get("MAX_TOKENS"))

""" LLM HANDLING """


def analyze_image(mode, contenuto, base64_image, client, script):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": env.get("AGENT_PROMPT", mode),
            },
        ]
        + script
        + generate_new_line(
            mode, contenuto, base64_image, len(script) == 0
        ),  # If the script is empty this is the starting image
        max_tokens=MAX_TOKENS,
    )
    response_text = response.choices[0].message.content
    return response_text


def generate_new_line(mode, contenuto, base64_image, first_prompt_bool):
    if first_prompt_bool:
        prompt = env.get("FIRST_IMAGE_PROMPT", mode)
    else:
        prompt = env.get("NEW_IMAGE_PROMPT", mode)

    if mode == "oracolo":
        prompt += (
            f"Il mio nome è {contenuto['nome']}. Ti chiedo questo: "
            + contenuto["richiesta"]
        )
    elif mode == "giudicami":
        prompt += contenuto["nome"]

    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{base64_image}",
                        "detail": "high",
                    },
                },
            ],
        },
    ]


""" TTS """


def play_audio(mode, text):
    audio = generate(
        text,
        voice=Voice(
            voice_id=env.get("ELEVENLABS_VOICE_ID", mode),
            settings=VoiceSettings(
                stability=float(env.get("ELEVENLABS_STABILITY")),
                similarity_boost=float(env.get("ELEVENLABS_SIMILARITY")),
                style=float(env.get("ELEVENLABS_STYLE")),
                use_speaker_boost=True,
            ),
        ),
        model="eleven_multilingual_v2",
    )

    unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    play(audio)


""" MAIN """


def main(
    from_error=False,
    text=None,
    debug_camera=False,
    debug_chat=False,
    manual_triggering=False,
):
    manual_triggering = True  # This version of narrator requires manual_triggering

    print("☕ Waking up Roberto... (narrator)")

    # Start camera.
    reader = get_camera("<video0>")
    # time.sleep(2) # Wait for the camera to initialize and adjust light levels

    capture(reader, debugging=debug_camera)  # loop until camera shows something
    # When debugging the camera, the above command loops in infinite
    if not from_error:
        print("👋 Hi!")
        audio_feedback.startup()

    # OpenAI client initialization
    client = OpenAI()

    # ElevenLabs API initialization
    set_api_key(env.get("ELEVENLABS_API_KEY"))

    max_times = int(env.get("MAX_TIMES"))
    count = 0

    # TTS error handling
    tts_error_occurred = False
    tts_error = None

    script = []
    last_record_name = ""
    last_record_time = None
    while count != max_times:

        if manual_triggering:
            # Check triggering
            record = db.fetch_record(debug_chat)

            with open(f"requests/{record['id']}.json", "w+") as file:
                json.dump(record, file, indent=4)

            contenuto = record["contenuto"]
            mode = record["azione"]
            if mode == "giudizio":
                mode = record["contenuto"]["modalita"]
            print()
            print("Nuova richiesta con contenuto:")
            print(contenuto)
            admin = contenuto["admin"]
            if isinstance(admin, str):
                admin = True if admin == "true" else False

            if not admin:
                if mode == "reliquia":
                    continue
                if contenuto["nome"] == last_record_name:
                    if last_record_time is not None:
                        if (
                            time.time() - last_record_time
                        ) < 300:  # 300 seconds = 5 minutes:
                            print("Alterniamoci ragazzi!")
                            audio_feedback.new_turn()
                            continue

            # New request received.
        else:
            mode = ""
            contenuto = {}
            raise Exception(
                "This version of the narrator doesn't work without manual-triggering"
            )

        if count == 0 and text is not None:
            text = text
        else:
            # analyze posture
            print("👀 Roberto is looking...")
            base64_image = capture(reader)

            print("🧠 Roberto is thinking...")
            text = analyze_image(mode, contenuto, base64_image, client, script=script)

        try:
            print("🎙️ Roberto says:")
            print(text)
            print(len(text))
            print(count_tokens(text))
            text = cut_to_n_words(text, int(MAX_TOKENS * 5 / 4))
            if not debug_chat:
                play_audio(mode, text)

        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break

        script = script + [{"role": "assistant", "content": text}]

        print("😝 Roberto is taking a break...")
        last_record_name = contenuto["nome"]
        last_record_time = time.time()
        time.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Turning off
    if not tts_error_occurred:
        audio_feedback.turnoff()

    reader.close()  # Turn off the camera

    if tts_error_occurred:
        maybe_start_alternative_narrator(
            tts_error, from_error, text, ".alt_narrator_providers/playht_narrator.py"
        )
    else:
        print(f"Reached the maximum of {max_times}... turning off the narrator.")
    sys.exit(0)


if __name__ == "__main__":
    from script_arguments import make_arguments

    args = make_arguments(parser_description="Narrator")

    main(**vars(args))
