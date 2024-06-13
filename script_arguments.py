import argparse

def make_arguments(parser_description):
    parser = argparse.ArgumentParser(description=parser_description)

    # Boolean
    parser.add_argument(
        "--from-error",
        action="store_true",
        help="If the script was run from an error of another narrator. It stores the Boolean value True if the specified argument is present in the command line and False otherwise."
    )

    # Text is conditionally required
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text to say at first instance of speech. Required if --from-error is True."
    )

    # Boolean
    parser.add_argument(
        "--debug-camera",
        action="store_true",
        help="If you want to debug the camera."
    )

    args = parser.parse_args()

    # Conditional requirement check
    if args.from_error and not args.text:
        parser.error("--text is required when --from-error is specified.")

    return args