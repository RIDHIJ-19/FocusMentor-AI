"""A quiet, decorative animated starfield -- twinkling dots, nothing more.

Kept deliberately light (small star count, ~12 fps) since this runs
alongside a background productivity app; paused entirely while the main
window is hidden to the tray so it costs nothing when minimized.
"""
import math
import random

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

_STAR_COUNT = 60
_FRAME_INTERVAL_MS = 80  # ~12 fps
_STAR_COLORS = ["#E8ECF7", "#22D3EE", "#EC4899"]


class StarfieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._rng = random.Random(42)
        self._stars = [
            {
                "x": self._rng.random(),
                "y": self._rng.random(),
                "radius": self._rng.uniform(0.6, 1.8),
                "phase": self._rng.uniform(0, math.tau),
                "speed": self._rng.uniform(0.03, 0.08),
                "color": self._rng.choice(_STAR_COLORS),
            }
            for _ in range(_STAR_COUNT)
        ]
        self._tick = 0

        self._timer = QTimer(self)
        self._timer.setInterval(_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def pause(self) -> None:
        self._timer.stop()

    def resume(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def _on_tick(self) -> None:
        self._tick += 1
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0B0E1A"))

        w, h = self.width(), self.height()
        for star in self._stars:
            brightness = 0.35 + 0.65 * (
                0.5 + 0.5 * math.sin(star["phase"] + self._tick * star["speed"])
            )
            color = QColor(star["color"])
            color.setAlphaF(max(0.0, min(1.0, brightness)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            center = QPointF(star["x"] * w, star["y"] * h)
            painter.drawEllipse(center, star["radius"], star["radius"])
