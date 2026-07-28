"""'Get Mentor Insight' — AI (or local) coaching feedback on recent progress."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox

from app.db.repository import TaskRepository
from app.services.ai_service import AIService


class MentorInsightDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mentor Insight")
        self.setMinimumSize(420, 260)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Based on your recent sessions:"))

        self.insight_text = QTextEdit()
        self.insight_text.setReadOnly(True)
        layout.addWidget(self.insight_text, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.insight_text.setPlainText("Thinking...")
        self.repaint()

        repo = TaskRepository()
        recent_tasks = repo.get_recent(days=14)
        insight = AIService().generate_insight(recent_tasks)
        self.insight_text.setPlainText(insight)
