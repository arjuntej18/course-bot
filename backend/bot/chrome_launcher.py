# Launches the dedicated Chrome instance used by the automation bot.

import subprocess
import time

from backend.config import DEBUG_PORT


CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PROFILE_DIR = r"C:\Users\ravitej\chrome-bot-profile"


def launch_chrome():
    command = [
        CHROME_PATH,
        "--remote-debugging-port=9222",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={PROFILE_DIR}",
    ]

    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(3)

    return True