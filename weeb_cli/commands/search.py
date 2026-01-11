from rich.console import Console
from weeb_cli.i18n import i18n
from weeb_cli.ui.header import show_header

console = Console()

def search_anime():
    console.clear()
    show_header(i18n.get("menu.options.search"))
    console.print("[yellow]Work in progress...[/yellow]")
    input(i18n.get("common.continue_key"))
