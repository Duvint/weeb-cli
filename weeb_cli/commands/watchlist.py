from rich.console import Console
from weeb_cli.i18n import i18n

console = Console()

def open_watchlist():
    console.print("[yellow]Work in progress...[/yellow]")
    input(i18n.get("common.continue_key"))
