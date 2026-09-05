# Connects to Chrome and locates the active Springboard course page.

from playwright.sync_api import Playwright

from backend.config import DEBUG_PORT


def connect_browser(playwright: Playwright):
    return playwright.chromium.connect_over_cdp(DEBUG_PORT)


def get_course_page(context):
    for page in context.pages:
        try:
            if "onwingspan.com" in page.url.lower():
                return page
        except Exception:
            pass

    if context.pages:
        return context.pages[0]

    return None
