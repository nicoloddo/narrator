# TTS Provider System

The narrator system has been refactored to use a modular TTS provider architecture, allowing easy switching between different text-to-speech services.

## Architecture

### Core Components

1. **Base Provider Interface** (`providers/base_provider.py`)
   - `TTSProvider`: Synchronous TTS interface
   - `AsyncTTSProvider`: Asynchronous TTS interface

2. **Provider Factory** (`providers/provider_factory.py`)
   - Creates provider instances
   - Manages provider discovery
   - Supports environment variable configuration

3. **Provider Implementations**
   - `ElevenLabsProvider`: ElevenLabs TTS service
   - `PlayHTProvider`: PlayHT TTS service

## Usage

### Command Line

```bash
# Use ElevenLabs (default)
python narrator.py --provider-name elevenlabs

# Use PlayHT
python narrator.py --provider-name playht

# Use environment variable
export TTS_PROVIDER=playht
python narrator.py
```

### Dedicated Scripts

```bash
# ElevenLabs narrator
python elevenlabs_narrator.py

# PlayHT async narrator  
python playht_narrator.py
```

### Environment Configuration

Set the `TTS_PROVIDER` environment variable to specify the default provider:
```bash
export TTS_PROVIDER=elevenlabs  # or "playht"
```

## Available Providers

- **elevenlabs**: ElevenLabs TTS service (synchronous)
- **playht**: PlayHT TTS service (asynchronous)

## Provider Requirements

### ElevenLabs
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID` 
- `ELEVENLABS_STABILITY`
- `ELEVENLABS_SIMILARITY`
- `ELEVENLABS_STYLE`

### PlayHT
- `PLAYHT_USER_ID`
- `PLAYHT_API_KEY`
- `PLAYHT_VOICE_ID`

## Error Handling

The system includes automatic fallback:
1. If the primary provider fails, the system attempts to use an alternative provider
2. ElevenLabs ↔ PlayHT fallback is automatic
3. Error details are logged for troubleshooting

## Adding New Providers

1. Create a new provider class inheriting from `TTSProvider` or `AsyncTTSProvider`
2. Implement required methods: `initialize()`, `play_audio()`, `cleanup()`, `provider_name`
3. Add the provider to `ProviderFactory.PROVIDERS` dictionary
4. Configure required environment variables

## Migration from Legacy System

The old `alt_narrator_providers/playht_narrator.py` has been updated to redirect to the new system for backward compatibility. All legacy functionality is preserved while using the new provider architecture.

## File Structure

```
providers/
├── __init__.py
├── base_provider.py          # Abstract interfaces
├── provider_factory.py       # Provider factory
├── elevenlabs_provider.py     # ElevenLabs implementation
└── playht_provider.py         # PlayHT implementation

# Narrator scripts
narrator.py                   # Main provider-agnostic narrator
elevenlabs_narrator.py        # Dedicated ElevenLabs script
playht_narrator.py           # Dedicated PlayHT async script

# Legacy compatibility
alt_narrator_providers/
└── playht_narrator.py       # Redirects to new system
``` 