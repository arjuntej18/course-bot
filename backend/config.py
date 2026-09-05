# Central configuration for the course bot.

from pathlib import Path

DEBUG_PORT = "http://127.0.0.1:9222"

DATA_DIR = Path("data")
PROGRESS_FILE = DATA_DIR / "progress.json"

SAVE_INTERVAL = 5
NETWORK_CHECK_INTERVAL = 10
STALL_TIMEOUT = 15

BREAK_MIN = 60
BREAK_MAX = 120

MAX_RETRIES = 5