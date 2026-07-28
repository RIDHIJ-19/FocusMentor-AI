"""Local app settings (currently just the optional Groq API key).

Lookup order for the API key (first one found wins):
  1. GROQ_API_KEY environment variable
  2. GROQ_API_KEY=... line in a .env file at the project root
  3. The Settings tab's saved value, via QSettings
     (HKCU\\Software\\FocusMentor AI\\FocusMentor AI on Windows -- same per-user
     registry idiom already used by autostart_service)

The .env file is never read or displayed by anything other than this
lookup -- it's meant to be edited directly by the user in a text editor,
not typed into the app's UI or seen by anyone else.
"""
import os
from typing import Optional

from PySide6.QtCore import QSettings

from app.config import APP_NAME, PROJECT_ROOT

_API_KEY_SETTING = "groq_api_key"
_ENV_FILE = PROJECT_ROOT / ".env"
_ENV_VAR_NAME = "GROQ_API_KEY"

_CHECKINS_ENABLED_SETTING = "checkins_enabled"
_VOICE_ENABLED_SETTING = "voice_notifications_enabled"


def _settings() -> QSettings:
    return QSettings(APP_NAME, APP_NAME)


def _read_dotenv_key() -> Optional[str]:
    if not _ENV_FILE.exists():
        return None
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == _ENV_VAR_NAME:
                value = value.strip().strip('"').strip("'")
                return value or None
    except OSError:
        return None
    return None


def get_api_key() -> Optional[str]:
    env_key = os.environ.get(_ENV_VAR_NAME)
    if env_key:
        return env_key.strip()

    dotenv_key = _read_dotenv_key()
    if dotenv_key:
        return dotenv_key

    value = _settings().value(_API_KEY_SETTING, "", type=str)
    return value or None


def get_settings_key() -> Optional[str]:
    """The raw value saved via the Settings tab / set_api_key, ignoring the
    env var and .env file. Used only to prefill/clear that UI field."""
    value = _settings().value(_API_KEY_SETTING, "", type=str)
    return value or None


def get_api_key_source() -> str:
    """Which source is currently supplying the key: 'env', 'dotenv',
    'settings', or 'none'. Used only to inform the Settings tab UI --
    never exposes the key value itself."""
    if os.environ.get(_ENV_VAR_NAME):
        return "env"
    if _read_dotenv_key():
        return "dotenv"
    if _settings().value(_API_KEY_SETTING, "", type=str):
        return "settings"
    return "none"


def set_api_key(key: str) -> None:
    _settings().setValue(_API_KEY_SETTING, key.strip())


def get_checkins_enabled() -> bool:
    """Whether mid-session check-in nudges are on. The interval itself is
    computed per-task as duration // 4 (see main_window._on_start_selected),
    not a fixed setting -- a 1-hour task checks in every ~15 min, a 2-hour
    task every ~30 min, so it scales instead of over- or under-nudging."""
    return _settings().value(_CHECKINS_ENABLED_SETTING, True, type=bool)


def set_checkins_enabled(enabled: bool) -> None:
    _settings().setValue(_CHECKINS_ENABLED_SETTING, enabled)


def get_voice_enabled() -> bool:
    """Whether notifications are also spoken aloud (offline TTS)."""
    return _settings().value(_VOICE_ENABLED_SETTING, True, type=bool)


def set_voice_enabled(enabled: bool) -> None:
    _settings().setValue(_VOICE_ENABLED_SETTING, enabled)
