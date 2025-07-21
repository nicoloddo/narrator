from utils.env_utils import get_agent_prompt
from utils.env_utils import get_env_var, get_first_image_prompt, get_new_image_prompt

MAX_TOKENS = int(get_env_var("MAX_TOKENS"))


def analyze_image(mode, message, base64_image, client, script):
    """Analyze image using OpenAI GPT-4o model synchronously."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": get_agent_prompt(mode),
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
    """Analyze image using OpenAI GPT-4o model asynchronously."""
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": get_agent_prompt(mode),
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
