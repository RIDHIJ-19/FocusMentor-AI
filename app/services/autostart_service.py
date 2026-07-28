"""Toggle launching the app automatically when Windows starts, via the
Registry Run key (HKCU, so no admin rights are needed)."""
import sys

from app.config import APP_NAME

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _winreg():
    import winreg

    return winreg


def is_enabled() -> bool:
    if sys.platform != "win32":
        return False
    winreg = _winreg()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    winreg = _winreg()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_WRITE) as key:
        if enabled:
            exe_path = f'"{sys.executable}" "{sys.argv[0]}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
