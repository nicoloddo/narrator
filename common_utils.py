import subprocess
import os
import re

from env_utils import get_first_image_prompt, get_new_image_prompt

# Create the frames folder if it doesn't exist
FRAMES_DIR = os.path.join(os.getcwd(), "frames")

""" **************************************************************************************************** """
""" ERROR HANDLING UTILS """


def maybe_start_alternative_narrator(e, from_error, text, alternative_narrator):
    if (
        from_error
    ):  # If this script was run from an error of another narrator, we stop it here to not create loops of runs.
        print(f"Error occurred: {e}\nThis was the alternative narrator..\n\n")
        raise e
    else:  # We start the alternative narrator.
        print(f"Error occurred: {e}\nStarting the alternative narrator.\n\n")
        command = ["python", alternative_narrator, "--from-error", "--text", text]
        subprocess.run(command)


""" **************************************************************************************************** """
""" LLM UTILS """


def generate_new_line(mode, message, base64_image, first_prompt_bool):
    if first_prompt_bool:
        prompt = get_first_image_prompt(mode)
    else:
        prompt = get_new_image_prompt(mode)

    if message and message.get("mode") == "ask_davide":
        if message.get("content"):
            prompt += f"\n\nThe person asks: {message['content']}. "

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


def cut_to_n_words(text, n):
    # Split the text into words
    words = text.split()

    # Get the first n words
    first_n_words = words[:n]

    # Join them back into a string if needed
    result = " ".join(first_n_words)

    return result


def count_tokens(text):
    # Convert text to lowercase and split into tokens
    tokens = re.findall(r"\b\w+\b", text.lower())

    # Return the total number of tokens
    return len(tokens)
