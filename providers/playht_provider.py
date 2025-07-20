import os
import asyncio
import time
import numpy as np

from pyht.async_client import AsyncClient
from pyht.client import TTSOptions
from pyht.protos import api_pb2
import simpleaudio as sa
from environment_selector import env

from .base_provider import AsyncTTSProvider

AUDIO_GENERATION_SAMPLE_RATE = 22050
MAX_MINUTES_PER_AUDIO = 4


class PlayHTProvider(AsyncTTSProvider):
    """PlayHT TTS provider implementation."""

    def __init__(self, mode: str = ""):
        super().__init__(mode)
        self.client = None
        self.options = None
        self._initialized = False

    async def initialize_async(self) -> None:
        """Initialize the PlayHT API client."""
        if not self._initialized:
            self.client = AsyncClient(
                user_id=env.get("PLAYHT_USER_ID"), api_key=env.get("PLAYHT_API_KEY")
            )
            self._initialized = True

    async def play_audio_async(self, text: str) -> None:
        """Generate and play audio using PlayHT TTS."""
        if not self._initialized:
            await self.initialize_async()

        self.options = self._create_playht_options()
        await self._async_play_audio(
            self.client.tts(text, voice_engine="PlayHT2.0-turbo", options=self.options)
        )

    async def cleanup_async(self) -> None:
        """Clean up PlayHT resources."""
        if self.client:
            await self.client.close()

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "PlayHT"

    def _create_playht_options(self) -> TTSOptions:
        """Create PlayHT TTS options."""
        return TTSOptions(
            voice=os.environ.get("PLAYHT_VOICE_ID"),
            sample_rate=AUDIO_GENERATION_SAMPLE_RATE,
            format=api_pb2.FORMAT_WAV,
            speed=0.9,
        )

    def _calculate_buffer_size(
        self, duration_minutes: int, sample_rate: int, data_type
    ) -> int:
        """Calculate buffer size for audio streaming."""
        max_duration_seconds = duration_minutes * 60
        bytes_per_sample = np.dtype(data_type).itemsize
        return max_duration_seconds * sample_rate * bytes_per_sample

    async def _async_play_audio(self, data) -> None:
        """Play audio stream asynchronously."""
        max_minutes_per_audio = MAX_MINUTES_PER_AUDIO
        audio_sample_dtype = np.float16

        buff_size = self._calculate_buffer_size(
            max_minutes_per_audio, AUDIO_GENERATION_SAMPLE_RATE, audio_sample_dtype
        )
        ptr = 0
        start_time = time.time()
        buffer = np.empty(buff_size, audio_sample_dtype)
        audio = None
        i = -1

        async for chunk in data:
            i += 1
            if i == 0:
                start_time = time.time()
                continue  # Drop the first response, we don't want a header.
            elif i == 1:
                print("First audio byte received in:", time.time() - start_time)

            for sample in np.frombuffer(chunk, audio_sample_dtype):
                buffer[ptr] = sample
                ptr += 1

            if i == 5:
                # Give a 4 sample worth of breathing room before starting playback
                audio = sa.play_buffer(buffer, 1, 2, AUDIO_GENERATION_SAMPLE_RATE)

        # Calculate approximate runtime and wait for audio to finish
        approx_run_time = (
            ptr / AUDIO_GENERATION_SAMPLE_RATE * (11 / 10)
        )  # Add 1/10 buffer
        await asyncio.sleep(max(approx_run_time + (start_time - time.time()), 0))

        if audio is not None:
            audio.stop()
