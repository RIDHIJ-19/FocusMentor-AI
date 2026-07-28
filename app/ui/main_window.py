"""Main application window: task list, add-task, active session timer, dashboard."""
import logging
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedLayout,
    QTabWidget,
    QCheckBox,
    QMessageBox,
)

from app.config import (
    APP_NAME,
    MIN_CHECKIN_DURATION_MIN,
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
)
from app.db.repository import TaskRepository
from app.db.update_repository import UpdateRepository
from app.models.update import CHECKIN, COMPLETE
from app.services import autostart_service, motivation, settings_service
from app.services.ai_service import AIService, SHORTFALL, SUCCESS
from app.services.timer_service import TimerService
from app.services.notification_service import NotificationService
from app.ui.task_dialog import TaskDialog
from app.ui.complete_session_dialog import CompleteSessionDialog
from app.ui.checkin_dialog import CheckinDialog
from app.ui.ai_plan_dialog import AIPlanDialog
from app.ui.dashboard_widget import DashboardWidget
from app.ui.starfield_widget import StarfieldWidget
from app.ui.tray_icon import TrayIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(480, 620)

        self.repo = TaskRepository()
        self.update_repo = UpdateRepository()
        self.ai_service = AIService()
        self.timer_service = TimerService(self)
        self.timer_service.tick.connect(self._on_timer_tick)
        self.timer_service.checkin_due.connect(self._on_checkin_due)
        self.timer_service.finished.connect(self._on_timer_finished)

        self.active_task_id = None

        self.tray_icon = TrayIcon(self, APP_NAME)
        self.notification_service = NotificationService(self.tray_icon)
        self.tray_icon.show()

        self._cleanup_stale_sessions()

        self._build_ui()
        self.refresh()

    def _cleanup_stale_sessions(self) -> None:
        """Self-healing after a crash or force-quit: a task left
        'in_progress' whose time has clearly already run out can never
        resume (this is a fresh process with no active timer), so it would
        otherwise sit stuck forever. Auto-remove those instead."""
        removed = self.repo.delete_overdue_in_progress()
        if not removed:
            return
        for task in removed:
            logger.warning(
                "Auto-removed stale in-progress task_id=%d (%r) -- its %d min session "
                "started at %s and was never properly finished (likely a crash/force-quit).",
                task.id, task.name, task.duration_min, task.started_at,
            )
        names = ", ".join(t.name for t in removed)
        self.notification_service.notify(
            APP_NAME,
            f"Cleaned up {len(removed)} task(s) that didn't finish properly last time: {names}",
        )

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        central = QWidget()
        stack = QStackedLayout(central)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self.starfield = StarfieldWidget(central)
        stack.addWidget(self.starfield)

        foreground = QWidget()
        foreground.setObjectName("mainForeground")
        root = QVBoxLayout(foreground)
        root.setContentsMargins(14, 14, 14, 14)
        stack.addWidget(foreground)
        stack.setCurrentWidget(foreground)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # --- Plan tab ---
        plan_tab = QWidget()
        plan_layout = QVBoxLayout(plan_tab)

        header = QHBoxLayout()
        header.addWidget(QLabel("Today's Plan"))
        header.addStretch(1)
        ai_plan_button = QPushButton("Plan with AI")
        ai_plan_button.clicked.connect(self._on_plan_with_ai)
        header.addWidget(ai_plan_button)
        add_button = QPushButton("+ Add Task")
        add_button.clicked.connect(self._on_add_task)
        header.addWidget(add_button)
        plan_layout.addLayout(header)

        self.task_list = QListWidget()
        plan_layout.addWidget(self.task_list)

        session_row = QHBoxLayout()
        self.active_session_label = QLabel("No active session.")
        session_row.addWidget(self.active_session_label, 1)
        self.finish_early_button = QPushButton("Finish Early")
        self.finish_early_button.setEnabled(False)
        self.finish_early_button.clicked.connect(self._on_finish_early)
        session_row.addWidget(self.finish_early_button)
        plan_layout.addLayout(session_row)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("Start Selected")
        self.start_button.clicked.connect(self._on_start_selected)
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self._on_delete_selected)
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.delete_button)
        plan_layout.addLayout(action_row)

        self.tabs.addTab(plan_tab, "🚀 Plan")

        # --- Dashboard tab ---
        self.dashboard = DashboardWidget()
        self.tabs.addTab(self.dashboard, "📊 Dashboard")

        # --- Settings tab ---
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        self.autostart_checkbox = QCheckBox("Start automatically when Windows starts")
        self.autostart_checkbox.setChecked(autostart_service.is_enabled())
        self.autostart_checkbox.toggled.connect(self._on_toggle_autostart)
        settings_layout.addWidget(self.autostart_checkbox)

        settings_layout.addWidget(QLabel(""))
        self.checkins_checkbox = QCheckBox("Mid-session check-ins (quiet notification ~every 25% of session length)")
        self.checkins_checkbox.setChecked(settings_service.get_checkins_enabled())
        self.checkins_checkbox.toggled.connect(settings_service.set_checkins_enabled)
        settings_layout.addWidget(self.checkins_checkbox)
        settings_layout.addWidget(
            QLabel(
                "e.g. a 1-hour task checks in every ~15 min, a 2-hour task every ~30 min\n"
                f"(duration ÷ 4) — so longer sessions aren't interrupted more often.\n"
                f"Tasks under {MIN_CHECKIN_DURATION_MIN} minutes never get check-ins."
            )
        )

        settings_layout.addWidget(QLabel(""))
        self.voice_checkbox = QCheckBox("Speak notifications aloud (offline text-to-speech)")
        self.voice_checkbox.setChecked(settings_service.get_voice_enabled())
        self.voice_checkbox.toggled.connect(settings_service.set_voice_enabled)
        settings_layout.addWidget(self.voice_checkbox)
        settings_layout.addWidget(
            QLabel("Applies to session-start, check-in, and session-complete announcements.")
        )

        settings_layout.addWidget(QLabel(""))
        settings_layout.addWidget(QLabel("Groq API Key (optional, free — enables AI planning & insights)"))

        self.api_key_source_label = QLabel("")
        settings_layout.addWidget(self.api_key_source_label)

        api_key_row = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(settings_service.get_settings_key() or "")
        self.api_key_input.setPlaceholderText("gsk_...")
        save_key_button = QPushButton("Save")
        save_key_button.clicked.connect(self._on_save_api_key)
        api_key_row.addWidget(self.api_key_input)
        api_key_row.addWidget(save_key_button)
        settings_layout.addLayout(api_key_row)
        settings_layout.addWidget(
            QLabel(
                "Get a free key at console.groq.com. Without it, plans are parsed locally.\n"
                "Prefer not to type it here? Copy .env.example to .env in the project folder\n"
                "and paste it there instead — that always takes priority over this field."
            )
        )
        self._refresh_api_key_source_label()

        settings_layout.addStretch(1)
        self.tabs.addTab(settings_tab, "⚙️ Settings")

        self.setCentralWidget(central)

    # ---------- Data refresh ----------

    def refresh(self) -> None:
        tasks = self.repo.get_by_date()
        self.task_list.clear()
        for task in tasks:
            status_mark = {
                STATUS_NOT_STARTED: "○",
                STATUS_IN_PROGRESS: "▶",
                STATUS_COMPLETED: "✓",
            }.get(task.status, "○")
            text = f"{status_mark} {task.name} ({task.duration_min} min)"
            if task.goal:
                text += f" — {task.goal}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.task_list.addItem(item)

        self.dashboard.refresh(
            tasks,
            self.repo.count_completed_all_time(),
            self.repo.count_distinct_active_days(),
            self.update_repo.get_recent(days=14),
        )

    def _announce(self, message: str) -> None:
        """Shows a tray notification and, if enabled, speaks it aloud."""
        self.notification_service.notify(APP_NAME, message)
        if settings_service.get_voice_enabled():
            self.notification_service.speak(message)

    # ---------- Task actions ----------

    def _on_add_task(self) -> None:
        dialog = TaskDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.repo.create(
                    name=data["name"],
                    goal=data["goal"],
                    duration_min=data["duration_min"],
                    start_time=data["start_time"],
                )
                self.refresh()

    def _on_plan_with_ai(self) -> None:
        dialog = AIPlanDialog(self)
        if dialog.exec():
            for task in dialog.get_selected_tasks():
                self.repo.create(
                    name=task["name"],
                    goal=task.get("goal"),
                    duration_min=task["duration_min"],
                    start_time=task.get("start_time"),
                )
            self.refresh()

    def _on_delete_selected(self) -> None:
        item = self.task_list.currentItem()
        if not item:
            return
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id == self.active_task_id:
            QMessageBox.warning(self, APP_NAME, "Stop the active session before deleting this task.")
            return
        self.repo.delete(task_id)
        self.refresh()

    def _on_start_selected(self) -> None:
        item = self.task_list.currentItem()
        if not item:
            QMessageBox.information(self, APP_NAME, "Select a task first.")
            return
        if self.active_task_id is not None:
            QMessageBox.information(self, APP_NAME, "A session is already running.")
            return

        task_id = item.data(Qt.ItemDataRole.UserRole)
        task = self.repo.get_by_id(task_id)
        if task.status == STATUS_COMPLETED:
            QMessageBox.information(self, APP_NAME, "This task is already completed.")
            return

        self.active_task_id = task_id
        self.repo.update_status(
            task_id, STATUS_IN_PROGRESS, started_at=datetime.now().isoformat(timespec="seconds")
        )
        checkins_on = settings_service.get_checkins_enabled() and task.duration_min >= MIN_CHECKIN_DURATION_MIN
        checkin_interval = task.duration_min // 4 if checkins_on else 0
        logger.info(
            "Starting session: task=%r duration_min=%d checkins_on=%s checkin_interval_min=%d",
            task.name, task.duration_min, checkins_on, checkin_interval,
        )
        self.timer_service.start(task.duration_min, checkin_interval)
        self.finish_early_button.setEnabled(True)
        flavor = motivation.get_line(motivation.SESSION_START)
        self._announce(f"Started: {task.name}. {flavor}")
        self.refresh()

    def _on_finish_early(self) -> None:
        if self.active_task_id is None:
            return
        logger.info("Finish Early clicked for task_id=%d", self.active_task_id)
        self.timer_service.stop()
        self._on_timer_finished()

    def _on_timer_tick(self, remaining_seconds: int) -> None:
        minutes, seconds = divmod(remaining_seconds, 60)
        task = self.repo.get_by_id(self.active_task_id) if self.active_task_id else None
        name = task.name if task else "Session"
        self.active_session_label.setText(f"{name}: {minutes:02d}:{seconds:02d} remaining")
        self.tray_icon.setToolTip(f"{APP_NAME} — {name}: {minutes:02d}:{seconds:02d}")

    def _on_checkin_due(self, elapsed_min: int, remaining_min: int) -> None:
        logger.info("checkin_due fired: elapsed_min=%d remaining_min=%d", elapsed_min, remaining_min)
        task_id = self.active_task_id
        task = self.repo.get_by_id(task_id) if task_id else None
        if not task:
            logger.warning("checkin_due fired but there is no active task -- ignoring.")
            return

        flavor = motivation.get_line(motivation.CHECKIN)
        self._announce(f"{task.name}: {elapsed_min} min in, {remaining_min} min left. {flavor}")

        self.showNormal()
        self.raise_()
        self.activateWindow()

        dialog = CheckinDialog(task.name, elapsed_min, remaining_min, flavor, self)
        dialog.exec()
        notes = dialog.get_notes()
        self.update_repo.add(task_id, CHECKIN, notes, elapsed_min=elapsed_min, remaining_min=remaining_min)
        logger.info("Stored check-in reply for task_id=%d: %r", task_id, notes)
        self.refresh()

    def _on_timer_finished(self) -> None:
        task_id = self.active_task_id
        task = self.repo.get_by_id(task_id) if task_id else None
        self.active_task_id = None
        self.active_session_label.setText("No active session.")
        self.tray_icon.setToolTip(APP_NAME)
        self.finish_early_button.setEnabled(False)

        if not task:
            return

        self.notification_service.play_alert_sound()
        self._announce(f"Your {task.name} session is complete. How did it go?")

        self.showNormal()
        self.raise_()
        self.activateWindow()

        dialog = CompleteSessionDialog(task.name, "", self)
        dialog.exec()
        notes = dialog.get_notes()
        self.repo.update_status(task_id, STATUS_COMPLETED, notes=notes or None)
        self.update_repo.add(task_id, COMPLETE, notes)
        logger.info("Stored completion reply for task_id=%d: %r", task_id, notes)

        verdict = self.ai_service.assess_completion(task.name, task.goal, notes)
        logger.info("Completion verdict for task_id=%d: %s", task_id, verdict)
        if verdict == SUCCESS:
            self.notification_service.play_success_jingle()
            self._announce(motivation.get_line(motivation.CELEBRATION))
        elif verdict == SHORTFALL:
            self.notification_service.play_stern_alert()
            self._announce(motivation.get_line(motivation.FELL_SHORT))

        self.refresh()

    # ---------- Settings ----------

    def _on_toggle_autostart(self, checked: bool) -> None:
        autostart_service.set_enabled(checked)

    def _on_save_api_key(self) -> None:
        settings_service.set_api_key(self.api_key_input.text())
        self._refresh_api_key_source_label()
        QMessageBox.information(self, APP_NAME, "API key saved.")

    def _refresh_api_key_source_label(self) -> None:
        source = settings_service.get_api_key_source()
        text = {
            "env": "Active key source: GROQ_API_KEY environment variable.",
            "dotenv": "Active key source: .env file (this field below is unused while .env has a value).",
            "settings": "Active key source: this field.",
            "none": "No API key configured yet.",
        }[source]
        self.api_key_source_label.setText(text)

    # ---------- Window behavior: minimize to tray instead of closing ----------

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
        self.notification_service.notify(
            APP_NAME, "Still running in the background. Use the tray icon to quit."
        )

    def hideEvent(self, event) -> None:
        self.starfield.pause()
        super().hideEvent(event)

    def showEvent(self, event) -> None:
        self.starfield.resume()
        super().showEvent(event)
