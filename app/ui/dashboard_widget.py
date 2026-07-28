"""Today's progress + simple long-term stats."""
from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QPushButton,
)

from app.config import STATUS_COMPLETED
from app.models.task import Task
from app.models.update import CHECKIN
from app.ui.mentor_insight_dialog import MentorInsightDialog


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.addWidget(self._section_title("Today's Progress"))

        self.progress_label = QLabel("0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        progress_row = QHBoxLayout()
        progress_row.addWidget(self.progress_bar, 1)
        progress_row.addWidget(self.progress_label)
        layout.addLayout(progress_row)

        self.checklist = QListWidget()
        layout.addWidget(self.checklist)

        layout.addWidget(self._divider())
        layout.addWidget(self._section_title("Long-Term Progress"))

        self.completed_all_time_label = QLabel("Sessions completed (all time): 0")
        self.active_days_label = QLabel("Days with a completed session: 0")
        layout.addWidget(self.completed_all_time_label)
        layout.addWidget(self.active_days_label)

        insight_button = QPushButton("Get Mentor Insight")
        insight_button.clicked.connect(self._on_get_insight)
        layout.addWidget(insight_button)

        layout.addWidget(self._divider())
        layout.addWidget(self._section_title("Recent Updates"))
        self.updates_list = QListWidget()
        layout.addWidget(self.updates_list)

        layout.addStretch(1)

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        label.setFont(font)
        return label

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def refresh(
        self,
        tasks: List[Task],
        completed_all_time: int,
        active_days: int,
        recent_updates: List[dict] = (),
    ) -> None:
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == STATUS_COMPLETED)
        pct = int((completed / total) * 100) if total else 0

        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"{pct}%")

        self.checklist.clear()
        for task in tasks:
            mark = "✓" if task.status == STATUS_COMPLETED else "○"
            item = QListWidgetItem(f"{mark} {task.name} - {task.status.replace('_', ' ').title()}")
            self.checklist.addItem(item)

        self.completed_all_time_label.setText(f"Sessions completed (all time): {completed_all_time}")
        self.active_days_label.setText(f"Days with a completed session: {active_days}")

        self.updates_list.clear()
        if not recent_updates:
            self.updates_list.addItem(QListWidgetItem("No check-in or session replies yet."))
        for update in recent_updates:
            when = datetime.fromisoformat(update["created_at"]).strftime("%b %d %H:%M")
            if update["kind"] == CHECKIN:
                kind_label = f"checkin, {update['elapsed_min']}m in"
            else:
                kind_label = "complete"
            note = update["note"] or "(no reply)"
            text = f"[{when}] {update['task_name']} ({kind_label}): {note}"
            self.updates_list.addItem(QListWidgetItem(text))

    def _on_get_insight(self) -> None:
        dialog = MentorInsightDialog(self)
        dialog.exec()
