import re
import json
from typing import List, Optional
from hashlib import md5
from base64 import b64decode

from weeb_cli.providers.base import (
    BaseProvider,
    AnimeResult,
    AnimeDetails,
    Episode,
    StreamLink
)
from weeb_cli.providers.registry import register_provider

BASE_URL = "https://turkanime.co"
_session = None
_key_cache = None


def _get_session():
    global _session
    if _session is None:
        try:
            from curl_cffi import requests as curl_requests
            _session = curl_requests.Session(impersonate="firefox")
        except ImportError:
            import requests
            _session = requests.Session()
    return _session


def _fetch(path: str) -> str:
    session = _get_session()
    url = f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = session.get(url, headers=headers, timeout=30)
        return response.text
    except Exception:
        return ""


def _obtain_key() -> bytes:
    global _key_cache
    if _key_cache:
        return _key_cache
    
    try:
        embed_html = _fetch("/embed/#/url/")
        js_files = re.findall(r"/embed/js/embeds\..*?\.js", embed_html)
        if len(js_files) < 2:
            return b""
        
        js1 = _fetch(js_files[1])
        js1_imports = re.findall("[a-z0-9]{16}", js1)
        
        j2 = _fetch(f'/embed/js/embeds.{js1_imports[0]}.js')
        if "'decrypt'" not in j2 and len(js1_imports) > 1:
            j2 = _fetch(f'/embed/js/embeds.{js1_imports[1]}.js')
        
        match = re.search(
            r'function a\d_0x[\w]{1,4}\(\){var _0x\w{3,8}=\[(.*?)\];', j2
        )
        if not match:
            return b""
        
        obfuscate_list = match.group(1)
        _key_cache = max(
            obfuscate_list.split("','"),
            key=lambda i: len(re.sub(r"\\x\d\d", "?", i))
        ).encode()
        return _key_cache
    except Exception:
        return b""


def _decrypt_cipher(key: bytes, data: bytes) -> str:
    try:
        from Crypto.Cipher import AES
    except ImportError:
        return ""
    
    def salted_key(data: bytes, salt: bytes, output: int = 48):
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]
    
    def unpad(data: bytes) -> bytes:
        return data[:-(data[-1] if isinstance(data[-1], int) else ord(data[-1]))]
    
    try:
        b64 = b64decode(data)
        cipher = json.loads(b64)
        cipher_text = b64decode(cipher["ct"])
        iv = bytes.fromhex(cipher["iv"])
        salt = bytes.fromhex(cipher["s"])
        
        crypt = AES.new(salted_key(key, salt, output=32), iv=iv, mode=AES.MODE_CBC)
        return unpad(crypt.decrypt(cipher_text)).decode("utf-8")
    except Exception:
        return ""


def _get_real_url(url_cipher: str) -> str:
    key = _obtain_key()
    if not key:
        return ""
    
    plaintext = _decrypt_cipher(key, url_cipher.encode())
    if not plaintext:
        return ""
    
    try:
        return "https:" + json.loads(plaintext)
    except Exception:
        return ""


@register_provider("turkanime", lang="tr", region="TR")
class TurkAnimeProvider(BaseProvider):
    
    def __init__(self):
        super().__init__()
    
    def search(self, query: str) -> List[AnimeResult]:
        html = _fetch("/ajax/tamliste")
        if not html:
            return []
        
        matches = re.findall(r'/anime/(.*?)".*?animeAdi">(.*?)<', html)
        
        results = []
        query_lower = query.lower()
        
        for slug, title in matches:
            if query_lower in title.lower() or query_lower in slug.lower():
                results.append(AnimeResult(
                    id=slug,
                    title=title
                ))
        
        return results[:20]
    
    def get_details(self, anime_id: str) -> Optional[AnimeDetails]:
        html = _fetch(f'/anime/{anime_id}')
        if not html:
            return None
        
        title_match = re.findall(r'<title>(.*?)</title>', html)
        title = title_match[0] if title_match else anime_id
        
        img_match = re.findall(r'twitter.image" content="(.*?)"', html)
        cover = img_match[0] if img_match else None
        
        anime_id_match = re.findall(r'serilerb/(.*?)\.jpg', html)
        internal_id = anime_id_match[0] if anime_id_match else ""
        
        summary_match = re.findall(r'"ozet">(.*?)</p>', html)
        description = summary_match[0] if summary_match else None
        
        episodes = self._get_episodes_internal(internal_id) if internal_id else []
        
        return AnimeDetails(
            id=anime_id,
            title=title,
            description=description,
            cover=cover,
            episodes=episodes,
            total_episodes=len(episodes)
        )
    
    def get_episodes(self, anime_id: str) -> List[Episode]:
        html = _fetch(f'/anime/{anime_id}')
        if not html:
            return []
        
        anime_id_match = re.findall(r'serilerb/(.*?)\.jpg', html)
        internal_id = anime_id_match[0] if anime_id_match else ""
        
        if not internal_id:
            return []
        
        return self._get_episodes_internal(internal_id)
    
    def _get_episodes_internal(self, internal_id: str) -> List[Episode]:
        html = _fetch(f'/ajax/bolumler&animeId={internal_id}')
        if not html:
            return []
        
        matches = re.findall(r'/video/(.*?)\\?".*?title=.*?"(.*?)\\?"', html)
        
        episodes = []
        for i, (slug, title) in enumerate(matches, 1):
            ep_num = self._parse_episode_number(title, i)
            episodes.append(Episode(
                id=slug,
                number=ep_num,
                title=title
            ))
        
        return episodes
    
    def get_streams(self, anime_id: str, episode_id: str) -> List[StreamLink]:
        html = _fetch(f'/video/{episode_id}')
        if not html:
            return []
        
        streams = []
        
        video_matches = re.findall(
            r'/embed/#/url/(.*?)\?status=0".*?</span> ([^ ]*?) ?</button>',
            html
        )
        
        for cipher, player in video_matches:
            url = _get_real_url(cipher)
            if url and "turkanime" not in url:
                streams.append(StreamLink(
                    url=url,
                    quality="auto",
                    server=player
                ))
        
        return streams
    
    def _parse_episode_number(self, title: str, fallback: int) -> int:
        patterns = [
            r'(\d+)\.\s*[Bb]ölüm',
            r'[Bb]ölüm\s*(\d+)',
            r'[Ee]pisode\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return int(match.group(1))
        
        return fallback
