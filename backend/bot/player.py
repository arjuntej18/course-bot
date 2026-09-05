# Controls Springboard HTML5 video playback and Next Content navigation.

import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from backend.config import MAX_RETRIES


def get_video(page):
    for attempt in range(MAX_RETRIES):
        try:
            video = page.locator("video").first

            video.wait_for(
                state="visible",
                timeout=15000,
            )

            page.wait_for_function(
                """() => {
                    const v = document.querySelector("video");

                    return v &&
                           Number.isFinite(v.duration) &&
                           v.duration > 0;
                }""",
                timeout=30000,
            )

            return video

        except Exception:
            print(
                f"[VIDEO] Video not ready "
                f"(attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(2)

    return None


def get_video_state(video):
    try:
        return video.evaluate(
            """
            v => ({
                currentTime: v.currentTime,
                duration: v.duration,
                paused: v.paused,
                ended: v.ended,
                readyState: v.readyState
            })
            """
        )

    except Exception:
        return None


def start_video(page, video, saved_position=0):
    state = get_video_state(video)

    if not state:
        return False

    current = state["currentTime"]
    duration = state["duration"]

    if state["ended"] or current >= duration - 2:
        print("[VIDEO] Video is already at the end.")
        return True

    if saved_position and saved_position > current + 2:
        resume_position = min(float(saved_position), duration - 3)

        if resume_position > current:
            print(
                f"[RECOVERY] Restoring position: "
                f"{resume_position:.1f}s"
            )

            try:
                video.evaluate(
                    "(v, pos) => { v.currentTime = pos; }",
                    resume_position,
                )
                page.wait_for_timeout(500)

            except Exception as exc:
                print(f"[RECOVERY] Seek failed: {exc}")

    for attempt in range(MAX_RETRIES):
        try:
            video.evaluate(
                """
                v => {
                    const p = v.play();
                    if (p) {
                        p.catch(() => {});
                    }
                }
                """
            )

            page.wait_for_timeout(1000)

            state = get_video_state(video)

            if state and not state["paused"]:
                print("[VIDEO] Playback started.")
                return True

        except Exception as exc:
            print(
                f"[VIDEO] Play attempt "
                f"{attempt + 1}/{MAX_RETRIES}: {exc}"
            )

        time.sleep(2)

    return False


def click_next(page):
    next_button = page.get_by_role(
        "button",
        name="next content",
    ).first

    if next_button.count() == 0:
        print("[COURSE] Next Content button not found.")
        return False

    if not next_button.is_enabled():
        print("[COURSE] Next Content button disabled.")
        return False

    old_url = page.url
    print("[COURSE] Moving to next video...")

    try:
        next_button.click(timeout=5000)

    except PlaywrightTimeoutError:
        print("[COURSE] Normal click timed out.")

    except Exception as exc:
        print(f"[COURSE] Click error: {exc}")

    try:
        page.wait_for_function(
            "oldUrl => window.location.href !== oldUrl",
            arg=old_url,
            timeout=5000,
        )

        print("[COURSE] Navigation detected.")
        return True

    except PlaywrightTimeoutError:
        pass

    print("[COURSE] Using DOM click fallback...")

    try:
        next_button.evaluate("(button) => button.click()")

    except Exception as exc:
        print(f"[COURSE] DOM click failed: {exc}")
        return False

    try:
        page.wait_for_function(
            "oldUrl => window.location.href !== oldUrl",
            arg=old_url,
            timeout=15000,
        )

        print("[COURSE] Navigation successful.")
        return True

    except PlaywrightTimeoutError:
        print("[COURSE] Navigation did not occur.")
        return False
