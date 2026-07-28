"""Desktop notifications, sound alerts, and spoken (offline TTS) announcements."""
import logging
import subprocess
import sys

from PySide6.QtWidgets import QSystemTrayIcon

logger = logging.getLogger(__name__)

_SPEAK_SCRIPT = "import sys, pyttsx3; e = pyttsx3.init(); e.say(sys.argv[1]); e.runAndWait()"

# Short, locally-generated tones (winsound.Beep) -- no bundled/copyrighted
# audio needed. Cheerful ascending arpeggio for success, low descending
# "buzz" for a shortfall. Same subprocess isolation as _SPEAK_SCRIPT.
_JINGLE_SCRIPT = (
    "import winsound as w\n"
    "for f, d in [(523, 120), (659, 120), (784, 120), (1047, 220)]:\n"
    "    w.Beep(f, d)\n"
)
_BUZZER_SCRIPT = (
    "import winsound as w\n"
    "for f, d in [(220, 260), (165, 380)]:\n"
    "    w.Beep(f, d)\n"
)


class NotificationService:
    def __init__(self, tray_icon: QSystemTrayIcon):
        self._tray_icon = tray_icon
        self._child_processes: list = []

    def notify(self, title: str, message: str) -> None:
        logger.info("Notification: %s - %s", title, message)
        if not QSystemTrayIcon.supportsMessages():
            logger.warning("This system reports no support for tray notifications.")
        if not self._tray_icon.isVisible():
            logger.warning("Tray icon is not visible -- notification may not display.")
        self._tray_icon.showMessage(
            title, message, QSystemTrayIcon.MessageIcon.Information, 8000
        )

    def play_alert_sound(self) -> None:
        if sys.platform == "win32":
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def speak(self, text: str) -> None:
        """Speaks text aloud via offline TTS (pyttsx3/SAPI5 on Windows --
        free, no internet, no API key). Best-effort: logs and no-ops on
        failure instead of breaking the calling notification flow.

        Runs in a short-lived child process rather than in-process. pyttsx3's
        SAPI5 driver uses COM (via comtypes), and after hours of repeated
        init/speak cycles in the same process this was observed to segfault
        the whole app -- likely COM apartment state getting corrupted and
        then colliding with Qt's own native window-activation calls. A
        subprocess fully isolates that COM state per announcement; the
        Qt main process can never crash because of it. Also non-blocking,
        which is a bonus over the old in-process runAndWait() call."""
        logger.info("Speaking: %s", text)
        self._run_isolated([sys.executable, "-c", _SPEAK_SCRIPT, text], "Text-to-speech")

    def play_success_jingle(self) -> None:
        """Short cheerful ascending tone sequence -- locally generated
        (winsound.Beep), no bundled/copyrighted audio."""
        logger.info("Playing success jingle")
        self._run_isolated([sys.executable, "-c", _JINGLE_SCRIPT], "Success jingle")

    def play_stern_alert(self) -> None:
        """Short low descending 'buzz' -- locally generated (winsound.Beep)."""
        logger.info("Playing stern alert")
        self._run_isolated([sys.executable, "-c", _BUZZER_SCRIPT], "Stern alert")

    def _run_isolated(self, args: list, label: str) -> None:
        """Fires a short-lived child process and forgets it (non-blocking).
        Same isolation rationale as speak(): keep anything touching Windows
        audio/COM APIs out of the main Qt process."""
        try:
            self._child_processes = [p for p in self._child_processes if p.poll() is None]
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._child_processes.append(process)
        except Exception as exc:
            logger.warning("%s failed: %s", label, exc)
