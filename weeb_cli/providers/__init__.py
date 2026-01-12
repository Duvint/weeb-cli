from weeb_cli.providers.base import BaseProvider
from weeb_cli.providers.registry import (
    register_provider,
    get_provider,
    get_providers_for_lang,
    list_providers
)

from weeb_cli.providers import animecix

__all__ = [
    "BaseProvider",
    "register_provider", 
    "get_provider",
    "get_providers_for_lang",
    "list_providers"
]
