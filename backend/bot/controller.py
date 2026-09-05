# Coordinates playback, recovery, progress saving, and course navigation.

import random
import time
from threading import Event

from backend.config import (
    BREAK_MAX,
    BREAK_MIN,
    SAVE_INTERVAL,
    STALL_TIMEOUT,
)
from backend.bot.player import (
    click_next,
    get_video,
    get_video_state,
    start_video,
)
from backend.bot.recovery import (
    internet_available,
    load_progress,
    save_progress,
    wait_for_internet,
)
from backend.bot.state import BotState, StatusStore


class CourseBotController:
    def __init__(self):
        self.stop_event = Event()
        self.status = StatusStore()

    def stop(self):
        self.stop_event.set()
        self.status.update(
            state=BotState.STOPPED,
            message="Automation stopped.",
        )

    def reset_stop(self):
        self.stop_event.clear()

    def watch_video(self, page, saved_position=0):
        last_position = -1
        last_progress_time = time.time()
        last_saved = 0

        self.status.update(
            state=BotState.LOADING_VIDEO,
            message="Loading video.",
            current_url=page.url,
        )

        while not self.stop_event.is_set():
            video = get_video(page)

            if video is None:
                self.status.update(
                    state=BotState.RECOVERING,
                    message="Video unavailable. Recovering.",
                )

                if not internet_available():
                    self.status.update(
                        state=BotState.PAUSED_BY_NETWORK,
                        internet_connected=False,
                        message="Internet connection lost.",
                    )

                    if not wait_for_internet(
                        self.stop_event,
                        self.status,
                    ):
                        return False

                time.sleep(3)
                continue

            state = get_video_state(video)

            if not state:
                time.sleep(2)
                continue

            current = state["currentTime"]
            duration = state["duration"]

            self.status.update(
                position=current,
                duration=duration,
                current_url=page.url,
                browser_connected=True,
            )

            if state["ended"] or current >= duration - 1:
                print(
                    f"[VIDEO] Completed "
                    f"({duration:.1f}/{duration:.1f}s)"
                )

                save_progress(
                    page.url,
                    duration,
                    duration,
                    "completed",
                )

                self.status.update(
                    state=BotState.VIDEO_COMPLETED,
                    position=duration,
                    duration=duration,
                    last_checkpoint=duration,
                    message="Video completed.",
                )

                return True

            if state["paused"]:
                self.status.update(
                    state=BotState.RECOVERING,
                    message="Starting or resuming video.",
                )

                position_to_use = saved_position

                if current > 2:
                    position_to_use = current

                if not start_video(
                    page,
                    video,
                    position_to_use,
                ):
                    time.sleep(3)
                    continue

                saved_position = 0

            self.status.update(
                state=BotState.PLAYING,
                message="Video playing.",
                internet_connected=True,
            )

            now = time.time()

            if now - last_saved >= SAVE_INTERVAL:
                save_progress(
                    page.url,
                    current,
                    duration,
                    "playing",
                )

                self.status.update(
                    last_checkpoint=current,
                )

                print(
                    f"[PROGRESS] "
                    f"{current:.1f}s / "
                    f"{duration:.1f}s"
                )

                last_saved = now

            if abs(current - last_position) < 0.1:
                if time.time() - last_progress_time >= STALL_TIMEOUT:
                    print("[RECOVERY] Video appears stalled.")

                    save_progress(
                        page.url,
                        current,
                        duration,
                        "stalled",
                    )

                    self.status.update(
                        state=BotState.RECOVERING,
                        message="Video stalled. Recovering.",
                        last_checkpoint=current,
                    )

                    if not internet_available():
                        self.status.update(
                            state=BotState.PAUSED_BY_NETWORK,
                            internet_connected=False,
                            message="Internet connection lost.",
                        )

                        if not wait_for_internet(
                            self.stop_event,
                            self.status,
                        ):
                            return False

                    video = get_video(page)

                    if video:
                        start_video(
                            page,
                            video,
                            current,
                        )

                    last_progress_time = time.time()

            else:
                last_progress_time = time.time()

            last_position = current
            time.sleep(2)

        return False

    def run_course(self, page):
        self.reset_stop()

        while not self.stop_event.is_set():
            if not internet_available():
                self.status.update(
                    state=BotState.PAUSED_BY_NETWORK,
                    internet_connected=False,
                    message="Internet connection lost.",
                )

                if not wait_for_internet(
                    self.stop_event,
                    self.status,
                ):
                    return

            saved = load_progress()
            saved_position = 0

            if saved and saved.get("last_url") == page.url:
                saved_position = float(
                    saved.get("last_position", 0)
                )

                print(
                    f"[RECOVERY] Saved position: "
                    f"{saved_position:.1f}s"
                )

            completed = self.watch_video(
                page,
                saved_position,
            )

            if not completed:
                if self.stop_event.is_set():
                    return

                time.sleep(2)
                continue

            break_time = random.randint(
                BREAK_MIN,
                BREAK_MAX,
            )

            self.status.update(
                state=BotState.BREAK,
                message=f"Break for {break_time} seconds.",
            )

            for _ in range(break_time):
                if self.stop_event.is_set():
                    return
                time.sleep(1)

            self.status.update(
                state=BotState.NEXT_VIDEO,
                message="Moving to next content.",
            )

            if not click_next(page):
                self.status.update(
                    state=BotState.RECOVERING,
                    message="Next navigation failed. Retrying.",
                )

                time.sleep(5)
                continue

            page.wait_for_timeout(3000)

            save_progress(
                page.url,
                0,
                0,
                "new_video",
            )
