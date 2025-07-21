import os
import asyncio
import time
import numpy as np

from pyht.async_client import AsyncClient
from pyht.client import TTSOptions
from pyht.protos import api_pb2
import simpleaudio as sa
from utils.env_utils import get_env_var, get_playht_voice_id

from .base_provider import AsyncTTSProvider

AUDIO_GENERATION_SAMPLE_RATE = 22050
MAX_MINUTES_PER_AUDIO = 4


class PlayHTProvider(AsyncTTSProvider):
    """PlayHT TTS provider implementation."""

    def __init__(self):
        self.client = None
        self.options = None
        self._initialized = False

    async def initialize_async(self) -> None:
        """Initialize the PlayHT API client."""
        if not self._initialized:
            print("Initializing PlayHT client...")
            user_id = get_env_var("PLAYHT_USER_ID")
            api_key = get_env_var("PLAYHT_API_KEY")
            self.client = AsyncClient(user_id=user_id, api_key=api_key)
            self._initialized = True

    async def play_audio_async(self, text: str, mode: str = "") -> None:
        """Generate and play audio using PlayHT TTS."""
        if not self._initialized:
            await self.initialize_async()

        self.options = self._create_playht_options(mode)
        await self._async_play_audio(
            self.client.tts(text, voice_engine="Play3.0-mini", options=self.options)
        )

    async def cleanup_async(self) -> None:
        """Clean up PlayHT resources."""
        if self.client:
            await self.client.close()

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "PlayHT"

    def _create_playht_options(self, mode: str) -> TTSOptions:
        """Create PlayHT TTS options."""
        return TTSOptions(
            voice=get_playht_voice_id(mode),
            sample_rate=AUDIO_GENERATION_SAMPLE_RATE,
            format=api_pb2.FORMAT_WAV,
        )

    async def _async_play_audio(self, audio_stream):
        """Play audio from async stream."""
        # Collect audio data
        audio_data = b""
        async for chunk in audio_stream:
            if chunk.data:
                audio_data += chunk.data

        if not audio_data:
            print("No audio data received")
            return

        # Write to temporary file
        temp_file = "temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_data)

        try:
            # Play the audio file
            wave_obj = sa.WaveObject.from_wave_file(temp_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
