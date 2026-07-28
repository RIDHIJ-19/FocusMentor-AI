"""Mid-session check-in prompt: how's it going so far?"""
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QVBoxLayout

from app.ui.theme import ACCENT_MAGENTA
from app.ui.voice_reply_widget import VoiceReplyWidget


class CheckinDialog(QDialog):
    def __init__(self, task_name: str, elapsed_min: int, remaining_min: int, flavor_line: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Check-in")
        self.setMinimumWidth(400)

        self.reply = VoiceReplyWidget(
            placeholder="e.g. Going well, just started the second problem."
        )

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(
            QLabel(f"{task_name}: {elapsed_min} min in, {remaining_min} min left.\nHow's it going?")
        )
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
