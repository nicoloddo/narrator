import os
import sys
import base64
import time
import json

from openai import OpenAI

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
from providers.provider_factory import ProviderFactory
from providers.base_provider import TTSProvider, AsyncTTSProvider

MAX_TOKENS = int(env.get("MAX_TOKENS"))

""" LLM HANDLING """


def analyze_image(mode, message, base64_image, client, script):
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
            mode, message, base64_image, len(script) == 0
        ),  # If the script is empty this is the starting image
        max_tokens=MAX_TOKENS,
    )
    response_text = response.choices[0].message.content
    return response_text


def generate_new_line(mode, message, base64_image, first_prompt_bool):
    if first_prompt_bool:
        prompt = env.get("FIRST_IMAGE_PROMPT", mode)
    else:
        prompt = env.get("NEW_IMAGE_PROMPT", mode)

    if message["mode"] == "ask_davide":
        if message["content"]:
            prompt += f"\n\nThe person asks: {message['content']}. "

    # Here you can put additions to the prompt based on the content if you want

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


""" MAIN """


def main(
    from_error=False,
    text=None,
    debug_camera=False,
    debug_chat=False,
    manual_triggering=False,
    provider_name=None,
):
    manual_triggering = True  # This version of narrator requires manual_triggering

    print(f"☕ Waking up the narrator... (narrator)")

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

    max_times = int(env.get("MAX_TIMES"))
    count = 0

    # TTS error handling
    tts_error_occurred = False
    tts_error = None

    script = []
    message = None

    # Initialize TTS provider
    tts_provider = None
    try:
        tts_provider = ProviderFactory.create_provider(provider_name)
        tts_provider.initialize()
        print(f"🎵 Using {tts_provider.provider_name} TTS provider")
    except Exception as e:
        print(f"Failed to initialize TTS provider: {e}")
        tts_error_occurred = True
        tts_error = e

    while count != max_times and not tts_error_occurred:

        if manual_triggering:
            # Check triggering
            record = db.fetch_record(debug_chat)

            with open(f"requests/{record['id']}.json", "w+") as file:
                json.dump(record, file, indent=4)

            content = record["content"]
            mode = record["mode"]

            agent_name = env.get("AGENT_NAME", mode)
            message = {
                "content": content,
                "mode": mode,
            }
            print()
            print(f"New {mode} request with content:")
            print(content)
            # New request received.
        else:
            mode = ""
            agent_name = "Unknown"
            content = {}
            raise Exception(
                "This version of the narrator doesn't work without manual-triggering"
            )

        if count == 0 and text is not None:
            text = text
        else:
            # analyze posture
            print(f"👀 {agent_name} is looking...")
            base64_image = capture(reader)

            print(f"🧠 {agent_name} is thinking...")
            text = analyze_image(mode, message, base64_image, client, script=script)

        try:
            print(f"🎙️ {agent_name} says:")
            print(text)
            print(len(text))
            print(count_tokens(text))
            text = cut_to_n_words(text, int(MAX_TOKENS * 5 / 4))
            if not debug_chat and tts_provider:
                tts_provider.play_audio(text)

        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break

        script = script + [{"role": "assistant", "content": text}]

        print(f"😝 {agent_name} is taking a break...")
        time.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Cleanup
    if tts_provider:
        try:
            tts_provider.cleanup()
        except Exception as e:
            print(f"Warning: Error during TTS provider cleanup: {e}")

    # Turning off
    if not tts_error_occurred:
        audio_feedback.turnoff()

    reader.close()  # Turn off the camera

    if tts_error_occurred:
        # Try alternative provider
        alternative_provider = (
            "playht" if tts_provider.provider_name == "elevenlabs" else "elevenlabs"
        )
        print(f"Trying alternative TTS provider: {alternative_provider}")

        # Start alternative narrator with different provider
        import subprocess

        command = [
            "python",
            "narrator.py",
            "--from-error",
            "--text",
            text,
            "--provider-name",
            alternative_provider,
        ]
        subprocess.run(command)
    else:
        print(f"Reached the maximum of {max_times}... turning off the narrator.")
    sys.exit(0)


if __name__ == "__main__":
    from script_arguments import make_arguments

    args = make_arguments(parser_description="Narrator")

    main(**vars(args))
