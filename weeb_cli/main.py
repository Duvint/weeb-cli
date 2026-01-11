import typer
import questionary
from weeb_cli.ui.menu import show_main_menu
from weeb_cli.commands.hello import say_hello
from weeb_cli.commands.settings import open_settings
from weeb_cli.config import config
from weeb_cli.i18n import i18n
from weeb_cli.commands.setup import start_setup_wizard

app = typer.Typer(add_completion=False)

def run_setup():
    langs = {
        "Türkçe": "tr",
        "English": "en"
    }
    
    selected = questionary.select(
        "Select Language / Dil Seçiniz",
        choices=list(langs.keys()),
        use_indicator=True
    ).ask()
    
    if selected:
        lang_code = langs[selected]
        i18n.set_language(lang_code)
        
        start_setup_wizard()

@app.command()
def start():
    if not config.get("language"):
        run_setup()

    actions = {
        "hello": say_hello,
        "settings": open_settings
    }
    show_main_menu(actions)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        start()

if __name__ == "__main__":
    app()
