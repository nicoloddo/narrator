from abc import ABC, abstractmethod
from typing import Optional


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def play_audio(self, text: str, mode: str = "") -> None:
        """
        Generate and play audio from the given text.

        Args:
            text: The text to convert to speech

        Raises:
            Exception: If TTS generation or playback fails
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the TTS provider (API keys, configuration, etc.)."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass


class AsyncTTSProvider(ABC):
    """Abstract base class for async TTS providers."""

    @abstractmethod
    async def play_audio_async(self, text: str, mode: str = "") -> None:
        """
        Generate and play audio from the given text asynchronously.

        Args:
            text: The text to convert to speech

        Raises:
            Exception: If TTS generation or playback fails
        """
        pass

    @abstractmethod
    async def initialize_async(self) -> None:
        """Initialize the TTS provider asynchronously."""
        pass

    @abstractmethod
    async def cleanup_async(self) -> None:
        """Clean up resources when shutting down asynchronously."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
