# Handles internet checks and persistent progress recovery.

import json
import os
import time
import urllib.request
from pathlib import Path

from backend.config import NETWORK_CHECK_INTERVAL, PROGRESS_FILE


def ensure_data_dir():
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_progress(url, position, duration, status="playing"):
    ensure_data_dir()

    data = {
        "last_url": url,
        "last_position": round(float(position), 2),
        "duration": round(float(duration), 2),
        "status": status,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    temp_file = PROGRESS_FILE.with_suffix(".tmp")

    try:
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        os.replace(temp_file, PROGRESS_FILE)

    except Exception as exc:
        print(f"[WARNING] Could not save progress: {exc}")


def load_progress():
    if not PROGRESS_FILE.exists():
        return None

    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception as exc:
        print(f"[WARNING] Could not read progress: {exc}")
        return None


def internet_available():
    try:
        request = urllib.request.Request(
            "https://www.google.com/generate_204",
            method="HEAD",
        )

        with urllib.request.urlopen(request, timeout=5):
            return True

    except Exception:
        return False


def wait_for_internet(stop_event=None, status_store=None):
    if status_store:
        status_store.update(
            internet_connected=False,
            message="Internet unavailable. Waiting for connection.",
        )

    print("[NETWORK] Internet unavailable.")
    print("[NETWORK] Waiting for connection...")

    while True:
        if stop_event and stop_event.is_set():
            return False

        if internet_available():
            print("[NETWORK] Internet restored.")

            if status_store:
                status_store.update(
                    internet_connected=True,
                    message="Internet restored.",
                )

            return True

        time.sleep(NETWORK_CHECK_INTERVAL)
