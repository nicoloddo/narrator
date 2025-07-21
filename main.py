import argparse
import asyncio
import sys
from narrator import Narrator


def make_arguments(parser_description):
    parser = argparse.ArgumentParser(description=parser_description)

    # Boolean
    parser.add_argument(
        "--from-error",
        action="store_true",
        help="If the script was run from an error of another narrator. It stores the Boolean value True if the specified argument is present in the command line and False otherwise.",
    )

    # Text is conditionally required
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text to say at first instance of speech. Required if --from-error is True.",
    )

    # Boolean
    parser.add_argument(
        "--debug-camera", action="store_true", help="If you want to debug the camera."
    )

    parser.add_argument(
        "--debug-movement",
        action="store_true",
        help="If you want to debug movement detection specifically.",
    )

    parser.add_argument(
        "--debug-chat", action="store_true", help="If you want to debug the chat model."
    )

    parser.add_argument(
        "--provider-name",
        type=str,
        default=None,
        help="TTS provider to use (elevenlabs, playht). If not specified, uses TTS_PROVIDER env var or defaults to elevenlabs.",
    )

    args = parser.parse_args()

    # Conditional requirement check
    if args.from_error and not args.text:
        parser.error("--text is required when --from-error is specified.")

    return args


async def main_async(**kwargs):
    """Async main function using the new Narrator class."""
    narrator = Narrator(**kwargs)

    try:
        await narrator.run()
    except Exception as e:
        print(f"Error running narrator: {e}")
        if narrator.tts_error_occurred:
            # Get the last response text if available
            last_text = kwargs.get("text", "Error occurred")
            await narrator.handle_tts_error(last_text)

    sys.exit(0)


if __name__ == "__main__":
    args = make_arguments(parser_description="Narrator")

    asyncio.run(main_async(**vars(args)))
