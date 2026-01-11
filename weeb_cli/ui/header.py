from rich import print
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

console = Console()

def show_header(title="Weeb API"):
    console.clear()
    
    console.print(Panel(Text(f" {title} ", style="bold white on blue"), expand=False, style="blue", padding=0))
    print()
