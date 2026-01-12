from weeb_cli.services.scraper import scraper

def get_streams(anime_id, episode_id):
    streams = scraper.get_streams(anime_id, episode_id)
    if not streams:
        return None
    
    return {
        "data": {
            "links": [
                {
                    "url": s.url,
                    "quality": s.quality,
                    "server": s.server
                }
                for s in streams
            ]
        }
    }
