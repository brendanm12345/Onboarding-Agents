import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    page = context.new_page()
    page.goto("https://www.kaggle.com/")
    page.get_by_role("button", name="OnboardedAgent").click()
    page.get_by_role("link", name="Your Work").click()
    page.get_by_role("textbox", name="Search Your Work").click()
    page.get_by_role("textbox", name="Search Your Work").fill("my last notebook")
    page.get_by_role("textbox", name="Search Your Work").press("ControlOrMeta+Shift+ArrowLeft")
    page.get_by_role("textbox", name="Search Your Work").press("ArrowRight")
    page.get_by_role("textbox", name="Search Your Work").fill("")
    page.locator("#site-content").get_by_role("link", name="notebookf66c1ad69f").click()

    # ---------------------
    context.storage_state(path="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
