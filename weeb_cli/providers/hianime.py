import json
import re
import urllib.request
from urllib.parse import quote, urlencode
from typing import List, Optional
from bs4 import BeautifulSoup

from weeb_cli.providers.base import (
    BaseProvider,
    AnimeResult,
    AnimeDetails,
    Episode,
    StreamLink
)
from weeb_cli.providers.registry import register_provider

BASE_URL = "https://hianime.to"
AJAX_URL = f"{BASE_URL}/ajax/v2"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Referer": BASE_URL
}


def _http_get(url: str, headers: dict = None, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _get_json(url: str, headers: dict = None, timeout: int = 15):
    try:
        data = _http_get(url, headers, timeout)
        return json.loads(data)
    except Exception:
        return None


def _get_html(url: str, headers: dict = None, timeout: int = 15) -> str:
    try:
        data = _http_get(url, headers, timeout)
        return data.decode('utf-8')
    except Exception:
        return ""


@register_provider("hianime", lang="en", region="US")
class HiAnimeProvider(BaseProvider):
    
    def __init__(self):
        super().__init__()
        self.headers = HEADERS.copy()
        
    def search(self, query: str) -> List[AnimeResult]:
        q = (query or "").strip()
        if not q:
            return []
        
        url = f"{BASE_URL}/search?keyword={quote(q)}"
        html = _get_html(url, self.headers)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for item in soup.select('.flw-item'):
            try:
                title_el = item.select_one('.film-name .dynamic-name')
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                href = title_el.get('href', '')
                anime_id = href.split('/')[-1].split('?')[0] if href else None
                
                if not anime_id or not title:
                    continue
                
                poster = item.select_one('.film-poster-img')
                cover = poster.get('data-src') if poster else None
                
                type_el = item.select_one('.fdi-item')
                anime_type = type_el.get_text(strip=True).lower() if type_el else "series"
                
                results.append(AnimeResult(
                    id=anime_id,
                    title=title,
                    type=self._parse_type(anime_type),
                    cover=cover
                ))
            except Exception:
                continue
        
        return results
    
    def get_details(self, anime_id: str) -> Optional[AnimeDetails]:
        url = f"{BASE_URL}/{anime_id}"
        html = _get_html(url, self.headers)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title_el = soup.select_one('.anisc-detail .film-name')
        title = title_el.get_text(strip=True) if title_el else anime_id
        
        desc_el = soup.select_one('.film-description .text')
        description = desc_el.get_text(strip=True) if desc_el else None
        
        poster_el = soup.select_one('.film-poster-img')
        cover = poster_el.get('src') if poster_el else None
        
        genres = []
        for genre_el in soup.select('.item-list a[href*="/genre/"]'):
            genres.append(genre_el.get_text(strip=True))
        
        episodes = self.get_episodes(anime_id)
        
        return AnimeDetails(
            id=anime_id,
            title=title,
            description=description,
            cover=cover,
            genres=genres,
            episodes=episodes,
            total_episodes=len(episodes)
        )
    
    def get_episodes(self, anime_id: str) -> List[Episode]:
        match = re.search(r'-(\d+)$', anime_id)
        if not match:
            return []
        
        show_id = match.group(1)
        url = f"{AJAX_URL}/episode/list/{show_id}"
        
        data = _get_json(url, self.headers)
        if not data or 'html' not in data:
            return []
        
        soup = BeautifulSoup(data['html'], 'html.parser')
        episodes = []
        
        for i, item in enumerate(soup.select('.ssl-item.ep-item')):
            try:
                href = item.get('href', '')
                ep_id = href.replace('/watch/', '').replace('?', '::') if href else None
                
                if not ep_id:
                    continue
                
                title = item.get('title', '')
                ep_num = i + 1
                
                episodes.append(Episode(
                    id=ep_id,
                    number=ep_num,
                    title=title
                ))
            except Exception:
                continue
        
        return episodes
    
    def get_streams(self, anime_id: str, episode_id: str) -> List[StreamLink]:
        ep_num = episode_id.split('ep=')[-1] if 'ep=' in episode_id else episode_id.split('::')[-1]
        
        servers_url = f"{AJAX_URL}/episode/servers?episodeId={ep_num}"
        servers_data = _get_json(servers_url, self.headers)
        
        if not servers_data or 'html' not in servers_data:
            return []
        
        soup = BeautifulSoup(servers_data['html'], 'html.parser')
        streams = []
        
        for server_item in soup.select('.server-item'):
            try:
                server_id = server_item.get('data-id')
                server_type = server_item.get('data-type', 'sub')
                server_name = server_item.select_one('a')
                server_name = server_name.get_text(strip=True).lower() if server_name else 'unknown'
                
                if not server_id:
                    continue
                
                sources_url = f"{AJAX_URL}/episode/sources?id={server_id}"
                sources_data = _get_json(sources_url, self.headers)
                
                if sources_data and 'link' in sources_data:
                    streams.append(StreamLink(
                        url=sources_data['link'],
                        quality="auto",
                        server=f"{server_name}-{server_type}",
                        headers={"Referer": BASE_URL}
                    ))
            except Exception:
                continue
        
        return streams
    
    def _parse_type(self, type_str: str) -> str:
        type_str = (type_str or "").lower()
        if "movie" in type_str:
            return "movie"
        if "ova" in type_str:
            return "ova"
        if "ona" in type_str:
            return "ona"
        if "special" in type_str:
            return "special"
        return "series"
