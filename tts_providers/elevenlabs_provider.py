import os
import base64

from elevenlabs import generate, play, set_api_key, voices, RateLimitError
from elevenlabs import Voice, VoiceSettings

from .base_provider import TTSProvider
from env_utils import (
    get_env_var,
    get_elevenlabs_voice_id,
    get_elevenlabs_stability,
    get_elevenlabs_similarity,
    get_elevenlabs_style,
)


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider implementation."""

    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the ElevenLabs API."""
        if not self._initialized:
            set_api_key(get_env_var("ELEVENLABS_API_KEY"))
            self._initialized = True

    def play_audio(self, text: str, mode: str = "") -> None:
        """Generate and play audio using ElevenLabs TTS."""
        if not self._initialized:
            self.initialize()

        audio = generate(
            text,
            voice=Voice(
                voice_id=get_elevenlabs_voice_id(mode),
                settings=VoiceSettings(
                    stability=float(get_elevenlabs_stability(mode)),
                    similarity_boost=float(get_elevenlabs_similarity(mode)),
                    style=float(get_elevenlabs_style(mode)),
                    use_speaker_boost=True,
                ),
            ),
            model="eleven_multilingual_v2",
        )

        # Save audio file for persistence
        unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
        dir_path = os.path.join("narration", unique_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "audio.wav")

        with open(file_path, "wb") as f:
            f.write(audio)

        # Play the audio
        play(audio)

    def cleanup(self) -> None:
        """Clean up ElevenLabs resources."""
        # ElevenLabs doesn't require explicit cleanup
        pass

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "ElevenLabs"
