"""Prompt shown when a timed session finishes, asking for a quick update."""
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QVBoxLayout

from app.ui.theme import ACCENT_MAGENTA
from app.ui.voice_reply_widget import VoiceReplyWidget


class CompleteSessionDialog(QDialog):
    def __init__(self, task_name: str, flavor_line: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Complete")
        self.setMinimumWidth(400)

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

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def closeEvent(self, event) -> None:
        self.reply.stop_recording_if_active()
        super().closeEvent(event)

    def get_notes(self) -> str:
        return self.reply.get_text()
