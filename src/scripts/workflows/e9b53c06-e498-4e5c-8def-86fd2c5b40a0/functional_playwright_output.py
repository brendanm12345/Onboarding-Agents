import re
from playwright.sync_api import Playwright, sync_playwright, expect

def add_item_to_todo_list(item: str, url: str, page):
    """Adds an item to the todo list. Must be called from the inputted url"""
    assert url is "https://demo.playwright.dev/todomvc/#/"
    page.get_by_role("textbox", name="What needs to be done?").click()
    page.get_by_role("textbox", name="What needs to be done?").fill(item)
    page.get_by_role("textbox", name="What needs to be done?").press("Enter")


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    currenturl = "https://demo.playwright.dev/todomvc/#/"
    page.goto(currenturl)
    add_item_to_todo_list(item="First todo item", url=currenturl, page=page)
    
    # refactor these to be well-described functions as well
    page.get_by_role("link", name="Active").click()
    page.get_by_role("checkbox", name="Toggle Todo").check()
    page.goto("https://demo.playwright.dev/todomvc/#/completed")
    page.get_by_role("button", name="Clear completed").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
