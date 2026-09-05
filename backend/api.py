
# FastAPI server connecting the dashboard to the course bot.

import socket
import subprocess
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from playwright.sync_api import sync_playwright

from backend.bot.browser import connect_browser, get_course_page
from backend.bot.controller import CourseBotController
from backend.bot.state import BotState


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE = Path.home() / "chrome-bot-profile"

DEBUG_PORT = 9222


app = FastAPI(title="Course Bot")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


controller = CourseBotController()

worker_thread = None


def chrome_debugging_available():
    # Check whether Chrome remote debugging is already running.
    try:
        with socket.create_connection(
            ("127.0.0.1", DEBUG_PORT),
            timeout=1,
        ):
            return True

    except Exception:
        return False


def launch_chrome():
    # Launch the dedicated Chrome profile used by the bot.

    if chrome_debugging_available():
        print("[CHROME] Chrome is already running.")
        return True

    print("[CHROME] Starting dedicated Chrome...")

    try:

        subprocess.Popen(
            [
                CHROME_PATH,
                f"--remote-debugging-port={DEBUG_PORT}",
                f"--user-data-dir={CHROME_PROFILE}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except Exception as exc:

        print(f"[CHROME] Failed to start Chrome: {exc}")
        return False

    for _ in range(20):

        if chrome_debugging_available():

            print(
                "[CHROME] Remote debugging is ready."
            )

            return True

        time.sleep(0.5)

    print(
        "[CHROME] Remote debugging did not start."
    )

    return False


def automation_worker():

    playwright = None

    try:

        controller.status.update(
            state=BotState.WAITING_FOR_CHROME,
            message="Starting Chrome...",
            error=None,
        )

        if not launch_chrome():

            controller.status.update(
                state=BotState.ERROR,
                message="Could not start Chrome.",
                error="Chrome remote debugging unavailable.",
            )

            return

        controller.status.update(
            message="Connecting to Chrome..."
        )

        playwright = sync_playwright().start()

        browser = connect_browser(playwright)

        context = browser.contexts[0]

        controller.status.update(
            state=BotState.CONNECTED,
            browser_connected=True,
            message="Chrome connected.",
        )

        page = get_course_page(context)

        if page is None:

            controller.status.update(
                state=BotState.ERROR,
                message=(
                    "No course page found. "
                    "Open a Springboard video and try again."
                ),
                error="No course page detected.",
            )

            return

        print(
            f"[COURSE] Detected page: {page.url}"
        )

        controller.status.update(
            current_url=page.url,
            message="Course page detected.",
        )

        # Start the existing Phase 1 automation.
        controller.run_course(page)

    except Exception as exc:

        print(
            f"[ERROR] Automation error: {exc}"
        )

        controller.status.update(
            state=BotState.ERROR,
            browser_connected=False,
            error=str(exc),
            message=f"Automation error: {exc}",
        )

    finally:

        controller.status.update(
            browser_connected=False
        )

        if playwright:

            try:
                playwright.stop()

            except Exception:
                pass


@app.get("/")
def home():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/status")
def get_status():

    return controller.status.snapshot()


@app.post("/start")
def start():

    global worker_thread

    if worker_thread and worker_thread.is_alive():

        return {
            "success": False,
            "message": "Automation is already running.",
        }

    controller.reset_stop()

    worker_thread = threading.Thread(
        target=automation_worker,
        daemon=True,
    )

    worker_thread.start()

    return {
        "success": True,
        "message": "Automation started.",
    }


@app.post("/stop")
def stop():

    controller.stop()

    return {
        "success": True,
        "message": "Stop requested.",
    }


@app.post("/retry")
def retry():

    global worker_thread

    if worker_thread and worker_thread.is_alive():

        return {
            "success": False,
            "message": "Automation is still running.",
        }

    controller.reset_stop()

    worker_thread = threading.Thread(
        target=automation_worker,
        daemon=True,
    )

    worker_thread.start()

    return {
        "success": True,
        "message": "Retry started.",
    }


@app.post("/restart")
def restart():

    global worker_thread

    controller.stop()

    if worker_thread and worker_thread.is_alive():

        worker_thread.join(timeout=5)

    controller.reset_stop()

    worker_thread = threading.Thread(
        target=automation_worker,
        daemon=True,
    )

    worker_thread.start()

    return {
        "success": True,
        "message": "Automation restarted.",
    }
