"""Prompt shown when a timed session finishes, asking for a quick update."""
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.services import rule_based_parser
from app.ui.theme import ACCENT_MAGENTA
from app.ui.voice_reply_widget import VoiceReplyWidget


class CompleteSessionDialog(QDialog):
    def __init__(self, task_name: str, flavor_line: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Complete")
        self.setMinimumWidth(400)
        self.extend_minutes = None

        self.reply = VoiceReplyWidget(
            placeholder="e.g. Solved two binary search problems but struggled with identifying the search space."
        )

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel(f"Your '{task_name}' session is complete.\nHow did it go?"))
        header.addStretch(1)
        header.addWidget(self.reply.mic_button)
        layout.addLayout(header)

        if flavor_line:
            flavor_label = QLabel(flavor_line)
            flavor_label.setStyleSheet(f"color: {ACCENT_MAGENTA}; font-weight: 600;")
            layout.addWidget(flavor_label)

        layout.addWidget(self.reply)
        layout.addWidget(QLabel("Not finished? Type/say how much more time you need, e.g. \"10 more minutes\"."))

        button_row = QHBoxLayout()
        self.extend_button = QPushButton("Need More Time")
        self.extend_button.clicked.connect(self._on_extend)
        button_row.addWidget(self.extend_button)
        button_row.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        button_row.addWidget(buttons)
        layout.addLayout(button_row)

    def _on_extend(self) -> None:
        minutes = rule_based_parser.extract_duration_minutes(self.reply.get_text())
        if minutes is None:
            self.reply.status_label.setText(
                "Couldn't tell how long -- try e.g. \"10 more minutes\" or \"half an hour\"."
            )
            return
        self.extend_minutes = max(1, min(minutes, 240))
        self.accept()

    def closeEvent(self, event) -> None:
        self.reply.stop_recording_if_active()

    def get_notes(self) -> str:
        return self.reply.get_text()

    def get_extend_minutes(self):
        return self.extend_minutes
