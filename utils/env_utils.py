import os
import dotenv
from models.narrator_mode import MODE_CONFIGS, NarratorMode

# Load base environment variables
dotenv.load_dotenv()

# Agent-specific environment files mapping
AGENT_ENV_FILES = {
    "davide": "agents/davide.env",
    "bortis": "agents/bortis.env",
    "piersilvio": "agents/piers.env",
}


def load_agent_env(agent_name):
    """Load agent-specific environment variables based on agent name."""
    if agent_name and agent_name in AGENT_ENV_FILES:
        dotenv.load_dotenv(AGENT_ENV_FILES[agent_name])


def get_agent_from_mode(mode):
    """Get agent name from mode configuration."""

    if isinstance(mode, str):
        try:
            mode_enum = NarratorMode(mode)
        except ValueError:
            return None
    else:
        mode_enum = mode

    mode_config = MODE_CONFIGS.get(mode_enum)
    return mode_config.agent if mode_config else None


def get_env_var(key, mode=None):
    """Get environment variable, loading agent-specific env if mode is provided."""
    if mode:
        load_agent_env(mode)
    return os.environ.get(key)


def get_agent_name(mode):
    """Get agent name for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_AGENT_NAME (e.g., DAVIDE_AGENT_NAME)
    env_var = f"{agent.upper()}_AGENT_NAME"
    return os.environ.get(env_var)


def get_agent_prompt(mode):
    """Get agent prompt for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_AGENT_PROMPT (e.g., DAVIDE_AGENT_PROMPT)
    env_var = f"{agent.upper()}_AGENT_PROMPT"
    return os.environ.get(env_var)


def get_first_image_prompt(mode):
    """Get first image prompt for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_FIRST_IMAGE_PROMPT (e.g., DAVIDE_FIRST_IMAGE_PROMPT)
    env_var = f"{agent.upper()}_FIRST_IMAGE_PROMPT"
    return os.environ.get(env_var)


def get_new_image_prompt(mode):
    """Get new image prompt for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Try convention: AGENT_NAME_NEW_IMAGE_PROMPT (e.g., DAVIDE_NEW_IMAGE_PROMPT)
    env_var = f"{agent.upper()}_NEW_IMAGE_PROMPT"
    result = os.environ.get(env_var)

    # If not found, fall back to FIRST_IMAGE_PROMPT (some agents use same prompt for both)
    if not result:
        env_var = f"{agent.upper()}_FIRST_IMAGE_PROMPT"
        result = os.environ.get(env_var)

    return result


def get_elevenlabs_voice_id(mode):
    """Get ElevenLabs voice ID for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_ELEVENLABS_VOICE_ID (e.g., DAVIDE_ELEVENLABS_VOICE_ID)
    env_var = f"{agent.upper()}_ELEVENLABS_VOICE_ID"
    return os.environ.get(env_var)


def get_elevenlabs_stability(mode):
    """Get ElevenLabs stability for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_ELEVENLABS_STABILITY (e.g., DAVIDE_ELEVENLABS_STABILITY)
    env_var = f"{agent.upper()}_ELEVENLABS_STABILITY"
    return os.environ.get(env_var)


def get_elevenlabs_similarity(mode):
    """Get ElevenLabs similarity for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_ELEVENLABS_SIMILARITY (e.g., DAVIDE_ELEVENLABS_SIMILARITY)
    env_var = f"{agent.upper()}_ELEVENLABS_SIMILARITY"
    return os.environ.get(env_var)


def get_elevenlabs_style(mode):
    """Get ElevenLabs style for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_ELEVENLABS_STYLE (e.g., DAVIDE_ELEVENLABS_STYLE)
    env_var = f"{agent.upper()}_ELEVENLABS_STYLE"
    return os.environ.get(env_var)


def get_playht_voice_id(mode):
    """Get PlayHT voice ID for the given mode."""
    agent = get_agent_from_mode(mode)
    if not agent:
        return None

    load_agent_env(agent)

    # Use convention: AGENT_NAME_PLAYHT_VOICE_ID (e.g., DAVIDE_PLAYHT_VOICE_ID)
    env_var = f"{agent.upper()}_PLAYHT_VOICE_ID"
    return os.environ.get(env_var)
