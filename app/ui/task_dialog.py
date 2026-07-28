"""Modal dialog for adding a new task to today's plan."""
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTimeEdit,
    QCheckBox,
)
from PySide6.QtCore import QTime


class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Task")
        self.setMinimumWidth(360)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. DSA Practice")

        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g. Complete Graph Algorithms")

        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 600)
        self.duration_input.setValue(60)
        self.duration_input.setSuffix(" min")

        self.set_start_time_checkbox = QCheckBox("Set a start time")
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime.currentTime())
        self.start_time_input.setEnabled(False)
        self.set_start_time_checkbox.toggled.connect(self.start_time_input.setEnabled)

        form = QFormLayout(self)
        form.addRow("Task name", self.name_input)
        form.addRow("Goal", self.goal_input)
        form.addRow("Duration", self.duration_input)
        form.addRow(self.set_start_time_checkbox, self.start_time_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self._result_data = None

    def _on_accept(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        self._result_data = {
            "name": name,
            "goal": self.goal_input.text().strip() or None,
            "duration_min": self.duration_input.value(),
            "start_time": (
                self.start_time_input.time().toString("HH:mm")
                if self.set_start_time_checkbox.isChecked()
                else None
            ),
        }
        self.accept()

    def get_data(self):
        return self._result_data
