import os
import base64

from elevenlabs import generate, play, set_api_key, voices, RateLimitError
from elevenlabs import Voice, VoiceSettings

from .base_provider import TTSProvider
from environment_selector import env


class ElevenLabsProvider(TTSProvider):
    """ElevenLabs TTS provider implementation."""

    def __init__(self, mode: str = ""):
        super().__init__(mode)
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the ElevenLabs API."""
        if not self._initialized:
            set_api_key(env.get("ELEVENLABS_API_KEY"))
            self._initialized = True

    def play_audio(self, text: str) -> None:
        """Generate and play audio using ElevenLabs TTS."""
        if not self._initialized:
            self.initialize()

        audio = generate(
            text,
            voice=Voice(
                voice_id=env.get("ELEVENLABS_VOICE_ID", self.mode),
                settings=VoiceSettings(
                    stability=float(env.get("ELEVENLABS_STABILITY", self.mode)),
                    similarity_boost=float(env.get("ELEVENLABS_SIMILARITY", self.mode)),
                    style=float(env.get("ELEVENLABS_STYLE", self.mode)),
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
