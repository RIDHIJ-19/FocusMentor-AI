"""Countdown timer for the active task session."""
from PySide6.QtCore import QObject, QTimer, Signal


class TimerService(QObject):
    tick = Signal(int)              # remaining_seconds
    checkin_due = Signal(int, int)  # elapsed_minutes, remaining_minutes
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._qtimer = QTimer(self)
        self._qtimer.setInterval(1000)
        self._qtimer.timeout.connect(self._on_tick)
        self._total_seconds = 0
        self._remaining_seconds = 0
        self._checkin_interval_seconds = 0
        self._next_checkin_seconds = None

    @property
    def is_running(self) -> bool:
        return self._qtimer.isActive()

    @property
    def remaining_seconds(self) -> int:
        return self._remaining_seconds

    def start(self, duration_min: int, checkin_interval_min: int = 0) -> None:
        self._total_seconds = max(duration_min, 0) * 60
        self._remaining_seconds = self._total_seconds
        self._checkin_interval_seconds = max(checkin_interval_min, 0) * 60

        if self._checkin_interval_seconds and self._checkin_interval_seconds < self._total_seconds:
            self._next_checkin_seconds = self._total_seconds - self._checkin_interval_seconds
        else:
            self._next_checkin_seconds = None

        self._qtimer.start()
        self.tick.emit(self._remaining_seconds)

    def stop(self) -> None:
        self._qtimer.stop()
        self._remaining_seconds = 0
        self._next_checkin_seconds = None

    def _on_tick(self) -> None:
        self._remaining_seconds -= 1

        if self._next_checkin_seconds is not None and self._remaining_seconds <= self._next_checkin_seconds:
            elapsed_min = round((self._total_seconds - self._remaining_seconds) / 60)
            remaining_min = round(self._remaining_seconds / 60)
            self.checkin_due.emit(elapsed_min, remaining_min)
            if self._next_checkin_seconds > self._checkin_interval_seconds:
                self._next_checkin_seconds -= self._checkin_interval_seconds
            else:
                self._next_checkin_seconds = None

        if self._remaining_seconds <= 0:
            self._qtimer.stop()
            self._remaining_seconds = 0
            self.tick.emit(0)
            self.finished.emit()
        else:
            self.tick.emit(self._remaining_seconds)
