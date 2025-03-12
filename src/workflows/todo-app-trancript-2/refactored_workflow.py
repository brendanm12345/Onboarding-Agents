import re
from playwright.sync_api import Playwright, sync_playwright, expect, Page


def open_browser(playwright: Playwright, headless: bool = False) -> Page:
    """
    Opens the browser and returns a new page.
    """
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    return context.new_page()


def navigate_to_url(page: Page, url: str) -> None:
    """
    Navigates to the specified URL.
    """
    assert url.startswith("http"), "URL should start with http or https"
    page.goto(url)


def add_todo_item(page: Page, item_text: str) -> None:
    """
    Adds a to-do item to the list by typing the text into the input box and pressing Enter.
    """
    todo_input = page.get_by_role("textbox", name="What needs to be done?")
    expect(todo_input).to_be_visible()
    todo_input.click()
    todo_input.fill(item_text)
    todo_input.press("Enter")


def navigate_to_section(page: Page, section_name: str) -> None:
    """
    Navigates to a section (e.g., 'All', 'Completed') using the link associated with the section name.
    """
    link = page.get_by_role("link", name=section_name)
    expect(link).to_be_visible()
    link.click()


def toggle_todo_completion(page: Page) -> None:
    """
    Toggles the completion checkbox of the first to-do item.
    """
    checkbox = page.get_by_role("checkbox", name=re.compile("Toggle Todo"))
    expect(checkbox).to_be_visible()
    checkbox.check()


def close_browser(page: Page) -> None:
    """
    Closes the browser and the page context.
    """
    page.context.close()
    page.browser.close()


def main_workflow() -> None:
    """
    Main workflow to demonstrate adding a to-do item, marking it complete, and navigating sections.
    This function orchestrates the overall workflow described in the speech transcript.
    """
    with sync_playwright() as playwright:
        page = open_browser(playwright)
        navigate_to_url(page, "https://demo.playwright.dev/todomvc/#/completed")

        # Add a to-do item
        add_todo_item(page, "first item")

        # Navigate to 'All' section and verify
        navigate_to_section(page, "All")

        # Mark the item as completed
        toggle_todo_completion(page)

        # Navigate to 'Completed' section to verify
        navigate_to_section(page, "Completed")

        # Close the browser
        close_browser(page)


if __name__ == "__main__":
    main_workflow()
