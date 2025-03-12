import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://demo.playwright.dev/todomvc/#/completed")
    page.get_by_role("textbox", name="What needs to be done?").click()
    page.get_by_role("textbox", name="What needs to be done?").fill("first item")
    page.get_by_role("textbox", name="What needs to be done?").press("Enter")
    page.get_by_role("link", name="All").click()
    page.get_by_role("checkbox", name="Toggle Todo").check()
    page.get_by_role("link", name="Completed").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
