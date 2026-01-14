import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from weeb_cli.config import config
from weeb_cli.services.progress import progress_tracker

class LocalLibrary:
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        if self._db is None:
            from weeb_cli.services.database import db
            self._db = db
        return self._db
    
    def get_all_sources(self) -> List[Dict]:
        sources = []
        
        download_dir = Path(config.get("download_dir"))
        if download_dir.exists():
            sources.append({
                "path": str(download_dir),
                "name": "İndirilenler",
                "type": "local",
                "available": True
            })
        
        for drive in self.db.get_external_drives():
            path = Path(drive["path"])
            sources.append({
                "path": drive["path"],
                "name": drive["name"],
                "type": "external",
                "available": path.exists()
            })
        
        return sources
    
    def scan_library(self, source_path: str = None) -> List[Dict]:
        if source_path:
            return self._scan_folder(Path(source_path))
        
        download_dir = Path(config.get("download_dir"))
        return self._scan_folder(download_dir)
    
    def scan_all_sources(self) -> List[Dict]:
        all_anime = []
        seen_titles = set()
        
        for source in self.get_all_sources():
            if not source["available"]:
                continue
            
            anime_list = self._scan_folder(Path(source["path"]))
            for anime in anime_list:
                anime["source"] = source["name"]
                anime["source_path"] = source["path"]
                
                key = anime["title"].lower()
                if key not in seen_titles:
                    seen_titles.add(key)
                    all_anime.append(anime)
        
        return sorted(all_anime, key=lambda x: x["title"].lower())
    
    def _scan_folder(self, folder: Path) -> List[Dict]:
        if not folder.exists():
            return []
        
        anime_list = []
        
        for anime_folder in folder.iterdir():
            if not anime_folder.is_dir():
                continue
            
            episodes = self._scan_anime_folder(anime_folder)
            if episodes:
                anime_list.append({
                    "title": anime_folder.name,
                    "path": str(anime_folder),
                    "episodes": episodes,
                    "episode_count": len(episodes)
                })
        
        return sorted(anime_list, key=lambda x: x["title"].lower())
    
    def _scan_anime_folder(self, folder: Path) -> List[Dict]:
        episodes = []
        video_extensions = {'.mp4', '.mkv', '.avi', '.webm', '.m4v'}
        
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in video_extensions:
                ep_num = self._extract_episode_number(file.name)
                episodes.append({
                    "filename": file.name,
                    "path": str(file),
                    "number": ep_num,
                    "size": file.stat().st_size
                })
        
        return sorted(episodes, key=lambda x: x["number"])
    
    def _extract_episode_number(self, filename: str) -> int:
        patterns = [
            r'S\d+B(\d+)',
            r'[Ee]p?(\d+)',
            r'[Bb]ölüm\s*(\d+)',
            r'[Ee]pisode\s*(\d+)',
            r'- (\d+)',
            r'\[(\d+)\]',
            r'(\d+)\.',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    
    def get_anime_progress(self, anime_title: str) -> Dict:
        slug = self._title_to_slug(anime_title)
        return progress_tracker.get_anime_progress(slug)
    
    def mark_episode_watched(self, anime_title: str, ep_number: int, total_episodes: int):
        slug = self._title_to_slug(anime_title)
        progress_tracker.mark_watched(slug, ep_number, title=anime_title, total_episodes=total_episodes)
    
    def _title_to_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug
    
    def get_next_episode(self, anime_title: str, episodes: List[Dict]) -> Optional[Dict]:
        progress = self.get_anime_progress(anime_title)
        last_watched = progress.get("last_watched", 0)
        
        for ep in episodes:
            if ep["number"] > last_watched:
                return ep
        
        return episodes[0] if episodes else None
    
    def format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def add_external_drive(self, path: str, name: str = None):
        self.db.add_external_drive(path, name)
    
    def remove_external_drive(self, path: str):
        self.db.remove_external_drive(path)
    
    def rename_external_drive(self, path: str, name: str):
        self.db.update_drive_name(path, name)
    
    def get_external_drives(self):
        return self.db.get_external_drives()

local_library = LocalLibrary()
