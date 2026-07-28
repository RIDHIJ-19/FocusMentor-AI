"""App-wide constants and paths."""
from pathlib import Path

APP_NAME = "FocusMentor AI"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"

DB_PATH = DATA_DIR / "mentor.db"

STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"

MIN_CHECKIN_DURATION_MIN = 15  # tasks shorter than this never get mid-session check-ins
