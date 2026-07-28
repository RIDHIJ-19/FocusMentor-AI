"""'Plan with AI' — type your day in free text, review the parsed tasks, add them."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
)

from app.services import settings_service
from app.services.ai_service import AIService
from app.services.voice_service import VoiceRecorder


class AIPlanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plan with AI")
        self.setMinimumSize(460, 480)
        self.ai_service = AIService()
        self.voice_recorder = VoiceRecorder()
        self._parsed_tasks = []

        layout = QVBoxLayout(self)

        input_header = QHBoxLayout()
        input_header.addWidget(QLabel("Describe your plan in your own words:"))
        input_header.addStretch(1)
        self.mic_button = QPushButton("🎤 Record")
        self.mic_button.clicked.connect(self._on_toggle_record)
        input_header.addWidget(self.mic_button)
        layout.addLayout(input_header)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "I want to spend 2 hours on DSA, 3 hours on my AI project, "
            "and 1 hour reading research papers."
        )
        self.input_text.setFixedHeight(90)
        layout.addWidget(self.input_text)

        self.generate_button = QPushButton("Generate Tasks")
        self.generate_button.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("Review and uncheck anything you don't want to add:"))
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
            existing = self.input_text.toPlainText().strip()
            self.input_text.setPlainText(f"{existing} {text}".strip())
            self.status_label.setText("Transcribed. Review the text, then Generate Tasks.")
        else:
            self.status_label.setText("Couldn't transcribe that — try again or type instead.")

    def closeEvent(self, event) -> None:
        if self.voice_recorder.is_recording:
            self.voice_recorder.stop()
        super().closeEvent(event)

    def _on_generate(self) -> None:
        text = self.input_text.toPlainText().strip()
        if not text:
            return

        self.generate_button.setEnabled(False)
        self.generate_button.setText("Thinking...")
        self.status_label.setText("")
        self.preview_list.clear()
        # Force a repaint so the "Thinking..." state is visible before the
        # (blocking) network/parse call below runs.
        self.repaint()

        result = self.ai_service.parse_plan_text(text)
        self._parsed_tasks = result.tasks

        self.generate_button.setEnabled(True)
        self.generate_button.setText("Generate Tasks")
        self.status_label.setText(self._status_for(result))

        if not self._parsed_tasks:
            self.status_label.setText(
                self.status_label.text() + " No tasks could be identified — try rephrasing."
            )
            return

        for task in self._parsed_tasks:
            label = f"{task['name']} — {task['duration_min']} min"
            if task.get("goal"):
                label += f" — {task['goal']}"
            if task.get("start_time"):
                label += f" — starts {task['start_time']}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.preview_list.addItem(item)

    @staticmethod
    def _status_for(result) -> str:
        if result.used_ai:
            return "Parsed with AI."
        if result.fallback_reason == "no_key":
            return "No Groq API key set — used basic parsing."
        if result.fallback_reason == "empty":
            return "AI found no tasks — used basic parsing."
        return f"AI request failed ({result.fallback_reason}) — used basic parsing."

    def get_selected_tasks(self) -> list:
        selected = []
        for i in range(self.preview_list.count()):
            item = self.preview_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(self._parsed_tasks[i])
        return selected
