"""Entry point: FocusMentor AI desktop app."""
import logging
import sys
from logging.handlers import RotatingFileHandler

# Imported before PySide6 on purpose: once PySide6 loads, its shibokensupport
# import hook intercepts every subsequent import in the process (even
# unrelated stdlib ones) for source inspection, which is slow enough to look
# like a hang. Pre-importing the heavy third-party deps here lets them (and
# their transitive stdlib imports like ipaddress/ssl) load at full speed and
# get cached in sys.modules before that hook is installed.
import numpy  # noqa: F401
import requests  # noqa: F401
import sounddevice  # noqa: F401

from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, LOG_FILE
from app.db.database import init_db
from app.ui import theme
from app.ui.main_window import MainWindow


def _configure_logging() -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main() -> None:
    _configure_logging()
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(theme.STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
