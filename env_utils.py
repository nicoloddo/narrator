import os
import dotenv

# Load base environment variables
dotenv.load_dotenv()

# Mode-specific agent environment files mapping
AGENT_ENV_FILES = {
    "ask_davide": "agents/davide.env",
    "ask_bortis": "agents/bortis.env",
    "look_piersilvio": "agents/piersilvio.env",
}


def load_agent_env(mode):
    """Load agent-specific environment variables based on mode."""
    if mode in AGENT_ENV_FILES:
        dotenv.load_dotenv(AGENT_ENV_FILES[mode])


def get_env_var(key, mode=None):
    """Get environment variable, loading agent-specific env if mode is provided."""
    if mode:
        load_agent_env(mode)
    return os.environ.get(key)


def get_agent_name(mode):
    """Get agent name for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_AGENT_NAME")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_AGENT_NAME")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_AGENT_NAME")
    return None


def get_agent_prompt(mode):
    """Get agent prompt for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_AGENT_PROMPT")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_AGENT_PROMPT")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_AGENT_PROMPT")
    return None


def get_first_image_prompt(mode):
    """Get first image prompt for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_FIRST_IMAGE_PROMPT")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_FIRST_IMAGE_PROMPT")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("GIUDICAMI_PIERSILVIO")
    return None


def get_new_image_prompt(mode):
    """Get new image prompt for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_NEW_IMAGE_PROMPT")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        # Bortis uses the same prompt for first and new
        return os.environ.get("BORTIS_FIRST_IMAGE_PROMPT")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        # Piersilvio uses the same prompt for first and new
        return os.environ.get("GIUDICAMI_PIERSILVIO")
    return None


def get_elevenlabs_voice_id(mode):
    """Get ElevenLabs voice ID for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_ELEVENLABS_VOICE_ID")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_ELEVENLABS_VOICE_ID")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_ELEVENLABS_VOICE_ID")
    return None


def get_elevenlabs_stability(mode):
    """Get ElevenLabs stability for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_ELEVENLABS_STABILITY")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_ELEVENLABS_STABILITY")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_ELEVENLABS_STABILITY")
    return None


def get_elevenlabs_similarity(mode):
    """Get ElevenLabs similarity for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_ELEVENLABS_SIMILARITY")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_ELEVENLABS_SIMILARITY")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_ELEVENLABS_SIMILARITY")
    return None


def get_elevenlabs_style(mode):
    """Get ElevenLabs style for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_ELEVENLABS_STYLE")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_ELEVENLABS_STYLE")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_ELEVENLABS_STYLE")
    return None


def get_playht_voice_id(mode):
    """Get PlayHT voice ID for the given mode."""
    if mode == "ask_davide":
        load_agent_env(mode)
        return os.environ.get("DAVIDE_PLAYHT_VOICE_ID")
    elif mode == "ask_bortis":
        load_agent_env(mode)
        return os.environ.get("BORTIS_PLAYHT_VOICE_ID")
    elif mode == "look_piersilvio":
        load_agent_env(mode)
        return os.environ.get("PIERSILVIO_PLAYHT_VOICE_ID")
    return None
