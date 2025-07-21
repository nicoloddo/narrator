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

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=True,
        help="Continue running when TTS errors occur instead of shutting down (default: True).",
    )

    args = parser.parse_args()

    # Conditional requirement check
    if args.from_error and not args.text:
        parser.error("--text is required when --from-error is specified.")

    # Handle continue_on_error logic
    if args.no_continue_on_error:
        args.continue_on_error = False
    # Convert hyphenated argument to underscore for Python
    args.continue_on_error = getattr(args, "continue_on_error", True)

    return args


async def main_async(**kwargs):
    """Async main function using the new Narrator class."""
    narrator = Narrator(**kwargs)

    try:
        await narrator.run()
    except Exception as e:
        print(f"Error running narrator: {e}")
        if narrator.tts_error_occurred:
            await narrator.handle_tts_error()

    sys.exit(0)


if __name__ == "__main__":
    args = make_arguments(parser_description="Narrator")

    asyncio.run(main_async(**vars(args)))
