# Adding New Agents to the Narrator System

The narrator system now uses a flexible, convention-based approach for managing agents. Here's how to add new agents:

## Step 1: Create Agent Environment File

Create a new `.env` file in the `agents/` folder with your agent's name (e.g., `agents/myagent.env`):

```bash
# agents/myagent.env

# Required fields
MYAGENT_AGENT_NAME="My Agent Display Name"
MYAGENT_AGENT_PROMPT="Your agent's personality and behavior description here"

# Voice configuration (at least one provider required)
MYAGENT_ELEVENLABS_VOICE_ID="your-elevenlabs-voice-id"
MYAGENT_ELEVENLABS_STABILITY="0.7"
MYAGENT_ELEVENLABS_SIMILARITY="0.8"
MYAGENT_ELEVENLABS_STYLE="0.5"

# Alternative: PlayHT configuration
MYAGENT_PLAYHT_VOICE_ID="your-playht-voice-id"

# Optional: Custom image prompts
MYAGENT_FIRST_IMAGE_PROMPT="Prompt for first interaction"
MYAGENT_NEW_IMAGE_PROMPT="Prompt for subsequent interactions"
```

## Step 2: Register Agent File

Add your agent to the `AGENT_ENV_FILES` mapping in `utils/env_utils.py`:

```python
AGENT_ENV_FILES = {
    "davide": "agents/davide.env",
    "bortis": "agents/bortis.env", 
    "piersilvio": "agents/piers.env",
    "myagent": "agents/myagent.env",  # <- Add your agent here
}
```

## Step 3: Add Mode (Optional)

If you want a dedicated mode for your agent, add it to `models/narrator_mode.py`:

```python
class NarratorMode(str, Enum):
    # ... existing modes ...
    ASK_MYAGENT = "ask_myagent"  # Add your mode

# Add mode configuration
MODE_CONFIGS = {
    # ... existing configs ...
    NarratorMode.ASK_MYAGENT: ModeConfig(
        mode=NarratorMode.ASK_MYAGENT,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.RECORD_TRIGGERED,
        sleep_interval=1.0,
        description="My agent interaction mode",
        agent="myagent",  # <- Links to your agent
    ),
}
```

## Environment Variable Naming Convention

The system uses a consistent naming pattern: `{AGENT_NAME_UPPERCASE}_{VARIABLE_TYPE}`

### Required Variables
- `{AGENT}_AGENT_NAME` - Display name for the agent
- `{AGENT}_AGENT_PROMPT` - Main personality/behavior prompt

### Voice Provider Variables
- `{AGENT}_ELEVENLABS_VOICE_ID` - ElevenLabs voice ID
- `{AGENT}_ELEVENLABS_STABILITY` - ElevenLabs stability setting
- `{AGENT}_ELEVENLABS_SIMILARITY` - ElevenLabs similarity setting  
- `{AGENT}_ELEVENLABS_STYLE` - ElevenLabs style setting
- `{AGENT}_PLAYHT_VOICE_ID` - PlayHT voice ID

### Optional Image Prompt Variables
- `{AGENT}_FIRST_IMAGE_PROMPT` - Prompt for first image analysis
- `{AGENT}_NEW_IMAGE_PROMPT` - Prompt for subsequent images (falls back to FIRST_IMAGE_PROMPT)

## Validation

Use the built-in validation to check your agent configuration:

```python
from utils.agent_utils import validate_agent

result = validate_agent("myagent")
if result["valid"]:
    print("Agent is properly configured!")
else:
    print("Issues found:", result["issues"])
```

## Example: Adding "Einstein" Agent

1. **Create `agents/einstein.env`:**
```bash
EINSTEIN_AGENT_NAME="Albert Einstein"
EINSTEIN_AGENT_PROMPT="You are Albert Einstein. Explain everything with scientific curiosity and wonder, often relating observations to physics principles."
EINSTEIN_ELEVENLABS_VOICE_ID="your-voice-id-here"
EINSTEIN_ELEVENLABS_STABILITY="0.8"
EINSTEIN_ELEVENLABS_SIMILARITY="0.9" 
EINSTEIN_ELEVENLABS_STYLE="0.3"
EINSTEIN_FIRST_IMAGE_PROMPT="Observe this scene with the eye of a physicist. What scientific principles do you see at work?"
```

2. **Register in `utils/env_utils.py`:**
```python
AGENT_ENV_FILES = {
    # ... existing agents ...
    "einstein": "agents/einstein.env",
}
```

3. **Add mode in `models/narrator_mode.py`:**
```python
ASK_EINSTEIN = "ask_einstein"

# In MODE_CONFIGS:
NarratorMode.ASK_EINSTEIN: ModeConfig(
    mode=NarratorMode.ASK_EINSTEIN,
    agent="einstein",
    # ... other config ...
),
```

That's it! The system will automatically discover and use your agent's configuration using the convention-based approach. 