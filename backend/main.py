# Runs the modular Springboard course bot from the command line.

from playwright.sync_api import sync_playwright

from backend.bot.browser import connect_browser, get_course_page
from backend.bot.controller import CourseBotController
from backend.bot.state import BotState


def main():
    controller = CourseBotController()

    print("=" * 60)
    print("SPRINGBOARD COURSE BOT - PHASE 1")
    print("=" * 60)

    with sync_playwright() as playwright:
        controller.status.update(
            state=BotState.WAITING_FOR_CHROME,
            message="Connecting to Chrome.",
        )

        print("[CHROME] Connecting to existing Chrome...")

        browser = connect_browser(playwright)
        context = browser.contexts[0]
        page = get_course_page(context)

        if page is None:
            print("[ERROR] No Springboard page found.")
            return

        controller.status.update(
            state=BotState.CONNECTED,
            message="Chrome and course page connected.",
            browser_connected=True,
            current_url=page.url,
        )

        print("[CONNECTED]")
        print(page.title())
        print(page.url)

        controller.run_course(page)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n[STOP] Bot stopped manually.")

    except Exception as exc:
        print(f"\n[FATAL ERROR] {exc}")
