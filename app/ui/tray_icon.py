"""System tray icon with Show/Quit context menu."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#4C6EF5"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(28)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "M")
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, app_name: str):
        super().__init__(_make_icon(), main_window)
        self._main_window = main_window
        self.setToolTip(app_name)

        menu = QMenu()
        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._show_main_window)
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(QApplication.quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_main_window()

    def _show_main_window(self) -> None:
        self._main_window.showNormal()
        self._main_window.raise_()
        self._main_window.activateWindow()
