import time
import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://demo.playwright.dev/todomvc/#/")
    time.sleep(1)
    page.get_by_role("textbox", name="What needs to be done?").click()
    time.sleep(1)
    page.get_by_role("textbox", name="What needs to be done?").fill("first item")
    time.sleep(1)
    page.get_by_role("textbox", name="What needs to be done?").press("Enter")
    time.sleep(1)
    page.get_by_role("checkbox", name="Toggle Todo").check()
    time.sleep(1)
    page.get_by_role("link", name="Completed").click()
    time.sleep(1)
    page.get_by_role("button", name="Clear completed").click()
    time.sleep(1)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
