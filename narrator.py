import os
import sys
import base64
import time
import json
import asyncio

from openai import OpenAI, AsyncOpenAI

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


async def analyze_image_async(mode, message, base64_image, client, script):
    response = await client.chat.completions.create(
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
        print(f"TTS error occurred: {tts_error}")

        # Try alternative provider
        alternative_provider = (
            "playht" if tts_provider.provider_name == "ElevenLabs" else "elevenlabs"
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


async def async_main(
    from_error=False,
    text=None,
    debug_camera=False,
    debug_chat=False,
    manual_triggering=False,
    provider_name=None,
):
    """Async version of main for async TTS providers."""
    manual_triggering = True  # This version of narrator requires manual_triggering

    print(f"☕ Waking up the async narrator... (narrator)")

    # Start camera.
    reader = get_camera("<video0>")
    # time.sleep(2) # Wait for the camera to initialize and adjust light levels

    capture(reader, debugging=debug_camera)  # loop until camera shows something
    # When debugging the camera, the above command loops in infinite
    if not from_error:
        print("👋 Hi!")
        audio_feedback.startup()

    # OpenAI client initialization
    client = AsyncOpenAI()

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
        if isinstance(tts_provider, AsyncTTSProvider):
            await tts_provider.initialize_async()
        else:
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

            os.makedirs("requests", exist_ok=True)
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
            text = await analyze_image_async(
                mode, message, base64_image, client, script=script
            )

        try:
            print(f"🎙️ {agent_name} says:")
            print(text)
            print(len(text))
            print(count_tokens(text))
            text = cut_to_n_words(text, int(MAX_TOKENS * 5 / 4))
            if not debug_chat and tts_provider:
                if isinstance(tts_provider, AsyncTTSProvider):
                    await tts_provider.play_audio_async(text)
                else:
                    tts_provider.play_audio(text)

        except Exception as e:
            tts_error_occurred = True
            tts_error = e
            break

        script = script + [{"role": "assistant", "content": text}]

        print(f"😝 {agent_name} is taking a break...")
        await asyncio.sleep(1)  # Wait a bit before sending a new image

        count += 1

    # Cleanup
    if tts_provider:
        try:
            if isinstance(tts_provider, AsyncTTSProvider):
                await tts_provider.cleanup_async()
            else:
                tts_provider.cleanup()
        except Exception as e:
            print(f"Warning: Error during TTS provider cleanup: {e}")

    # Turning off
    if not tts_error_occurred:
        audio_feedback.turnoff()

    # Turn off the camera in executor to avoid blocking
    await asyncio.get_running_loop().run_in_executor(None, reader.close)

    if tts_error_occurred:
        print(f"TTS error occurred: {tts_error}")

        # Try alternative provider
        alternative_provider = (
            "playht" if tts_provider.provider_name == "ElevenLabs" else "elevenlabs"
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


def run_narrator(**kwargs):
    """Wrapper function that determines whether to use sync or async main based on provider type."""
    provider_name = kwargs.get("provider_name")

    try:
        # Create a temporary provider to check its type
        temp_provider = ProviderFactory.create_provider(provider_name)

        if isinstance(temp_provider, AsyncTTSProvider):
            print("🔄 Detected async provider, using async mode...")
            asyncio.run(async_main(**kwargs))
        else:
            print("🔄 Detected sync provider, using sync mode...")
            main(**kwargs)

    except Exception as e:
        print(f"Error determining provider type: {e}")
        print("Falling back to sync mode...")
        main(**kwargs)


if __name__ == "__main__":
    from script_arguments import make_arguments

    args = make_arguments(parser_description="Narrator")

    run_narrator(**vars(args))
