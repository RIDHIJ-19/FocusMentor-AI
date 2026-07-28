"""Reusable text + voice (🎤) reply input.

Used by both the session-complete and check-in dialogs so the recording
state machine (start/stop/transcribe) isn't duplicated between them. The
mic button is exposed publicly so a containing dialog can place it in its
own header row next to a prompt label.
"""
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.services import settings_service
from app.services.ai_service import AIService
from app.services.voice_service import VoiceRecorder


class VoiceReplyWidget(QWidget):
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.ai_service = AIService()
        self.voice_recorder = VoiceRecorder()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.mic_button = QPushButton("🎤 Record")
        self.mic_button.clicked.connect(self._on_toggle_record)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(placeholder)
        layout.addWidget(self.text_input)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def _on_toggle_record(self) -> None:
        if not self.voice_recorder.is_recording:
            if not settings_service.get_api_key():
                self.status_label.setText("Voice input needs a Groq API key (Settings tab).")
                return
            try:
                self.voice_recorder.start()
            except Exception as exc:
                self.status_label.setText(f"Couldn't start recording: {exc}")
                return
            self.mic_button.setText("⏹ Stop")
            self.status_label.setText("Recording... click Stop when you're done.")
            return

        wav_bytes = self.voice_recorder.stop()
        self.mic_button.setText("Transcribing...")
        self.mic_button.setEnabled(False)
        self.repaint()

        text = self.ai_service.transcribe_audio(wav_bytes)

        self.mic_button.setEnabled(True)
        self.mic_button.setText("🎤 Record")

        if text:
            existing = self.text_input.toPlainText().strip()
            self.text_input.setPlainText(f"{existing} {text}".strip())
            self.status_label.setText("Transcribed.")
        else:
            self.status_label.setText("Couldn't transcribe that — try again or type instead.")

    def stop_recording_if_active(self) -> None:
        if self.voice_recorder.is_recording:
            self.voice_recorder.stop()

    def get_text(self) -> str:
        return self.text_input.toPlainText().strip()
