import time
from playwright.sync_api import Playwright, sync_playwright, Page, expect


def open_todo_app(page: Page, url: str = "https://demo.playwright.dev/todomvc/#/") -> None:
    """
    Opens the Todo application.

    Speech: It opens the app.
    """
    page.goto(url)
    assert page.url == url, "Failed to navigate to Todo app"


def add_todo_item(page: Page, item_text: str) -> None:
    """
    Selects the text box and adds a to-do item.

    Speech: So the first thing we're going to do is select this text box and add first item
    andpage. click Enter.
    """
    textbox = page.get_by_role("textbox", name="What needs to be done?")
    textbox.click()
    textbox.fill(item_text)
    textbox.press("Enter")
    todo_item = page.get_by_test_id("todo-item").filter(has_text=item_text)
    expect(todo_item).to_be_visible()


def check_off_todo_item(page: Page) -> None:
    """
    Checks off the first to-do item in the list.

    Speech: Now I'm going to show you how to check off the box.
    """
    checkbox = page.get_by_role("checkbox", name="Toggle Todo")
    checkbox.check()
    assert checkbox.is_checked(), "Failed to check off the to-do item"


def navigate_to_completed(page: Page) -> None:
    """
    Navigates to the Completed items section.

    Speech: And then if we navigate over to Completed,
    """
    page.get_by_role("link", name="Completed").click()
    time.sleep(1)
    assert page.url.endswith("completed"), "Failed to navigate to Completed section"


def clear_completed_items(page: Page) -> None:
    """
    Clears all completed to-do items.

    Speech: Now last thing is how we clear items.
    """
    page.get_by_role("button", name="Clear completed").click()
    expect(page.locator("//li")).not_to_be_visible(), "Failed to clear completed items"


def main() -> None:
    """
    Main workflow to demonstrate adding, checking, navigating, and clearing to-do items.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        open_todo_app(page)
        add_todo_item(page, "first item")
        check_off_todo_item(page)
        navigate_to_completed(page)
        clear_completed_items(page)

        context.close()
        browser.close()


if __name__ == "__main__":
    main()