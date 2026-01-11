from rich import print
from rich.text import Text
from rich.console import Console
from weeb_cli.config import config
from weeb_cli import __version__

console = Console()

def show_header(title="Weeb API"):
    console.clear()
    
    source = config.get("scraping_source", "local")
    display_source = "Weeb" if source == "local" else source
    
    text = Text()
    text.append(f" {title} ", style="bold white on blue")
    text.append(f" | {display_source} | v{__version__}", style="dim white")
    
    console.print(text, justify="left")
    print()
