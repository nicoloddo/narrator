import os
from typing import Union

from .base_provider import TTSProvider, AsyncTTSProvider
from .elevenlabs_provider import ElevenLabsProvider
from .playht_provider import PlayHTProvider


class ProviderFactory:
    """Factory for creating TTS provider instances."""

    PROVIDERS = {
        "elevenlabs": ElevenLabsProvider,
        "playht": PlayHTProvider,
    }

    @classmethod
    def create_provider(
        cls, provider_name: str = None
    ) -> Union[TTSProvider, AsyncTTSProvider]:
        """
        Create a TTS provider instance.

        Args:
            provider_name: Name of the provider to create. If None, uses TTS_PROVIDER env var.

        Returns:
            TTS provider instance

        Raises:
            ValueError: If provider_name is not supported
        """
        if provider_name is None:
            provider_name = os.environ.get("TTS_PROVIDER", "playht").lower()

        provider_name = provider_name.lower()

        if provider_name not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported provider '{provider_name}'. Available: {available}"
            )

        provider_class = cls.PROVIDERS[provider_name]
        return provider_class()

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls.PROVIDERS.keys())
