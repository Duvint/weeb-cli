from typing import List, Optional
from weeb_cli.config import config
from weeb_cli.providers import get_provider, get_default_provider, list_providers
from weeb_cli.providers.base import AnimeResult, AnimeDetails, Episode, StreamLink


class Scraper:
    
    def __init__(self):
        self._provider = None
        self._provider_name = None
    
    @property
    def provider(self):
        current_source = config.get("scraping_source", "")
        
        if self._provider_name != current_source:
            self._provider_name = current_source
            self._provider = get_provider(current_source)
            
            if not self._provider:
                lang = config.get("language", "tr")
                default = get_default_provider(lang)
                if default:
                    self._provider = get_provider(default)
                    self._provider_name = default
        
        return self._provider
    
    def search(self, query: str) -> List[AnimeResult]:
        if not self.provider:
            return []
        return self.provider.search(query)
    
    def get_details(self, anime_id: str) -> Optional[AnimeDetails]:
        if not self.provider:
            return None
        return self.provider.get_details(anime_id)
    
    def get_episodes(self, anime_id: str) -> List[Episode]:
        if not self.provider:
            return []
        return self.provider.get_episodes(anime_id)
    
    def get_streams(self, anime_id: str, episode_id: str) -> List[StreamLink]:
        if not self.provider:
            return []
        return self.provider.get_streams(anime_id, episode_id)
    
    def get_available_sources(self) -> List[dict]:
        return list_providers()
    
    def get_sources_for_lang(self, lang: str) -> List[str]:
        from weeb_cli.providers import get_providers_for_lang
        return get_providers_for_lang(lang)


scraper = Scraper()
