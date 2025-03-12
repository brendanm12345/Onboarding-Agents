import re
from playwright.sync_api import Playwright, sync_playwright, expect, Page


def open_todomvc(page: Page, section: str = "completed") -> None:
    """
    Open the TodoMVC demo app and navigate to a specific section.

    :param page: The Playwright page object.
    :param section: The section to open. Defaults to "completed".
    """
    url = f"https://demo.playwright.dev/todomvc/#/{section}"
    page.goto(url)
    assert page.url == url, f"Failed to open the {section} section"


def add_todo_item(page: Page, item_text: str) -> None:
    """
    Add a new to-do item to the list.

    :param page: The Playwright page object.
    :param item_text: The text of the to-do item to add.
    """
    textbox = page.get_by_role("textbox", name="What needs to be done?")
    textbox.click()
    textbox.fill(item_text)
    textbox.press("Enter")
    # Optionally verify the item was added, but this step is not necessary if add more assertion logic post just filling.


def navigate_to_section(page: Page, section_name: str) -> None:
    """
    Navigate to a specified section using the navigation links.

    :param page: The Playwright page object.
    :param section_name: The name of the section to navigate to (e.g., "All", "Active", "Completed").
    """
    page.get_by_role("link", name=section_name).click()
    # No assertion here, as the URL does not change (based on the provided code), but state could be interacted with if needed


def toggle_todo_item(page: Page) -> None:
    """
    Check the checkbox of a to-do item to mark it as completed.

    :param page: The Playwright page object.
    """
    checkbox = page.get_by_role("checkbox", name="Toggle Todo")
    checkbox.check()
    # Optional to verify if the item was moved is left out since no such action post-check is in this code


def main_workflow(playwright: Playwright) -> None:
    """
    Executes the main workflow described in the demonstration.

    :param playwright: The Playwright object.
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    open_todomvc(page)
    add_todo_item(page, "first item")
    navigate_to_section(page, "All")
    toggle_todo_item(page)
    navigate_to_section(page, "Completed")

    # Cleaning up the context and browser as final steps.
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        main_workflow(playwright)