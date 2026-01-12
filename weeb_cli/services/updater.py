import requests
from packaging import version
from weeb_cli import __version__
from rich.console import Console
import questionary
from weeb_cli.i18n import i18n
import sys
import os
import platform
import subprocess
import shutil
import webbrowser

console = Console()

def get_install_method():
    """Kurulum yöntemini tespit et"""
    # Frozen exe kontrolü (PyInstaller)
    if getattr(sys, 'frozen', False):
        return "exe"
    
    system = platform.system().lower()
    
    # Homebrew kontrolü (macOS/Linux)
    if shutil.which("brew"):
        try:
            result = subprocess.run(
                ["brew", "list", "weeb-cli"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "homebrew"
        except Exception:
            pass
    
    # AUR/yay kontrolü (Arch Linux)
    if shutil.which("yay"):
        try:
            result = subprocess.run(
                ["yay", "-Qi", "weeb-cli"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "aur"
        except Exception:
            pass
    
    # pacman kontrolü (Arch)
    if shutil.which("pacman"):
        try:
            result = subprocess.run(
                ["pacman", "-Qi", "weeb-cli"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "pacman"
        except Exception:
            pass
    
    # Scoop kontrolü (Windows)
    if system == "windows" and shutil.which("scoop"):
        try:
            result = subprocess.run(
                ["scoop", "list", "weeb-cli"],
                capture_output=True, text=True, timeout=10, shell=True
            )
            if "weeb-cli" in result.stdout:
                return "scoop"
        except Exception:
            pass
    
    # Chocolatey kontrolü (Windows)
    if system == "windows" and shutil.which("choco"):
        try:
            result = subprocess.run(
                ["choco", "list", "--local-only", "weeb-cli"],
                capture_output=True, text=True, timeout=10, shell=True
            )
            if "weeb-cli" in result.stdout:
                return "choco"
        except Exception:
            pass
    
    # pip kontrolü
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "weeb-cli"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "pip"
    except Exception:
        pass
    
    return "unknown"

def check_for_updates():
    """GitHub'dan son sürümü kontrol et"""
    try:
        url = "https://api.github.com/repos/ewgsta/weeb-cli/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_tag = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")
            
            if not latest_tag:
                return False, None, None
                
            current_ver = version.parse(__version__)
            latest_ver = version.parse(latest_tag)
            
            if latest_ver > current_ver:
                return True, latest_tag, html_url
                
    except Exception:
        pass
        
    return False, None, None

def run_update_command(cmd, shell=False):
    """Güncelleme komutunu çalıştır"""
    try:
        console.print(f"[cyan]{i18n.get('update.running')}: {' '.join(cmd) if isinstance(cmd, list) else cmd}[/cyan]")
        
        result = subprocess.run(
            cmd,
            capture_output=False,
            timeout=300,
            shell=shell
        )
        
        if result.returncode == 0:
            console.print(f"[green]{i18n.get('update.success')}[/green]")
            console.print(f"[dim]{i18n.get('update.restart_required')}[/dim]")
            return True
        else:
            return False
            
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]{i18n.get('update.timeout')}[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]{i18n.get('update.error')}: {e}[/red]")
        return False

def update_via_pip():
    """pip ile güncelle"""
    return run_update_command([sys.executable, "-m", "pip", "install", "--upgrade", "weeb-cli"])

def update_via_homebrew():
    """Homebrew ile güncelle"""
    return run_update_command(["brew", "upgrade", "weeb-cli"])

def update_via_aur():
    """AUR (yay) ile güncelle"""
    return run_update_command(["yay", "-Syu", "--noconfirm", "weeb-cli"])

def update_via_pacman():
    """pacman ile güncelle"""
    return run_update_command(["sudo", "pacman", "-Syu", "--noconfirm", "weeb-cli"])

def update_via_scoop():
    """Scoop ile güncelle"""
    return run_update_command("scoop update weeb-cli", shell=True)

def update_via_choco():
    """Chocolatey ile güncelle"""
    return run_update_command("choco upgrade weeb-cli -y", shell=True)

def open_releases_page(url):
    """GitHub releases sayfasını aç"""
    console.print(f"[blue]{i18n.get('update.opening')}[/blue]")
    if url:
        webbrowser.open(url)
    else:
        webbrowser.open("https://github.com/ewgsta/weeb-cli/releases/latest")

def update_prompt():
    """Güncelleme kontrolü ve prompt"""
    is_available, latest_ver, releases_url = check_for_updates()
    
    if not is_available:
        return
    
    console.clear()
    console.print(f"\n[green bold]{i18n.get('update.available')} (v{latest_ver})[/green bold]")
    console.print(f"[dim]{i18n.get('update.current')}: v{__version__}[/dim]\n")
    
    should_update = questionary.confirm(
        i18n.get("update.prompt"),
        default=True
    ).ask()
    
    if not should_update:
        return
    
    install_method = get_install_method()
    console.print(f"[dim]{i18n.get('update.detected')}: {install_method}[/dim]\n")
    
    success = False
    
    if install_method == "pip":
        success = update_via_pip()
    elif install_method == "homebrew":
        success = update_via_homebrew()
    elif install_method == "aur":
        success = update_via_aur()
    elif install_method == "pacman":
        success = update_via_pacman()
    elif install_method == "scoop":
        success = update_via_scoop()
    elif install_method == "choco":
        success = update_via_choco()
    else:
        # exe veya bilinmeyen kurulum - releases sayfasını aç
        console.print(f"[yellow]{i18n.get('update.manual_required')}[/yellow]")
        open_releases_page(releases_url)
        return
    
    if not success:
        console.print(f"\n[yellow]{i18n.get('update.fallback')}[/yellow]")
        open_releases_page(releases_url)
