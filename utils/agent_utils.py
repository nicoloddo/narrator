"""
Utilities for managing narrator agents and their configurations.
"""

import os
from typing import Optional, Dict, Any


def get_agent_env_var(agent_name: str, var_suffix: str) -> Optional[str]:
    """
    Get environment variable for an agent using naming convention.

    Args:
        agent_name: Name of the agent (e.g., "davide", "bortis")
        var_suffix: Suffix for the environment variable (e.g., "AGENT_NAME", "ELEVENLABS_VOICE_ID")

    Returns:
        Environment variable value or None if not found

    Example:
        get_agent_env_var("davide", "AGENT_NAME") -> gets DAVIDE_AGENT_NAME
    """
    if not agent_name:
        return None

    env_var = f"{agent_name.upper()}_{var_suffix}"
    return os.environ.get(env_var)


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    Get all available configuration for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        Dictionary containing all found configuration variables
    """
    if not agent_name:
        return {}

    # Standard configuration keys we look for
    config_keys = [
        "AGENT_NAME",
        "AGENT_PROMPT",
        "FIRST_IMAGE_PROMPT",
        "NEW_IMAGE_PROMPT",
        "ELEVENLABS_VOICE_ID",
        "ELEVENLABS_STABILITY",
        "ELEVENLABS_SIMILARITY",
        "ELEVENLABS_STYLE",
        "PLAYHT_VOICE_ID",
    ]

    config = {}
    for key in config_keys:
        value = get_agent_env_var(agent_name, key)
        if value is not None:
            config[key.lower()] = value

    return config


def list_available_agents() -> Dict[str, str]:
    """
    List all agents that have environment files available.

    Returns:
        Dictionary mapping agent names to their env file paths
    """
    from utils.env_utils import AGENT_ENV_FILES

    return AGENT_ENV_FILES.copy()


def validate_agent(agent_name: str) -> Dict[str, Any]:
    """
    Validate an agent configuration and return status.

    Args:
        agent_name: Name of the agent to validate

    Returns:
        Dictionary with validation results
    """
    from utils.env_utils import load_agent_env

    if not agent_name:
        return {"valid": False, "error": "Agent name cannot be empty"}

    # Load agent environment
    load_agent_env(agent_name)

    # Check for required fields
    agent_display_name = get_agent_env_var(agent_name, "AGENT_NAME")
    agent_prompt = get_agent_env_var(agent_name, "AGENT_PROMPT")

    issues = []
    if not agent_display_name:
        issues.append(f"Missing {agent_name.upper()}_AGENT_NAME")
    if not agent_prompt:
        issues.append(f"Missing {agent_name.upper()}_AGENT_PROMPT")

    # Check for at least one voice provider
    has_elevenlabs = get_agent_env_var(agent_name, "ELEVENLABS_VOICE_ID") is not None
    has_playht = get_agent_env_var(agent_name, "PLAYHT_VOICE_ID") is not None

    if not has_elevenlabs and not has_playht:
        issues.append(
            "No voice provider configured (missing both ELEVENLABS_VOICE_ID and PLAYHT_VOICE_ID)"
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "has_elevenlabs": has_elevenlabs,
        "has_playht": has_playht,
        "config": get_agent_config(agent_name),
    }
