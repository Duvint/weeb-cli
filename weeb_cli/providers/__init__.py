from weeb_cli.providers.base import BaseProvider
from weeb_cli.providers.registry import (
    register_provider,
    get_provider,
    get_providers_for_lang,
    list_providers
)

from weeb_cli.providers import animecix
from weeb_cli.providers import anizle
from weeb_cli.providers import turkanime

__all__ = [
    "BaseProvider",
    "register_provider", 
    "get_provider",
    "get_providers_for_lang",
    "list_providers"
]
