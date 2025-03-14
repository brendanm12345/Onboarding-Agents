import re
from playwright.sync_api import Playwright, sync_playwright, expect, Page

# Functions corresponding to distinct actions based on speech transcript and Playwright script

def navigate_to_login_page(page: Page) -> None:
    """
    Navigates to the login page of the WRDS website.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/")
    page.goto("https://wrds-www.wharton.upenn.edu/login")


def perform_login(page: Page, username: str, password: str) -> None:
    """
    Performs the login operation using provided username and password.

    :param page: The Playwright page object.
    :param username: The username for login.
    :param password: The password for login.
    """
    page.get_by_role("textbox", name="Username").fill(username)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()


def handle_two_factor_authentication(page: Page, passcode: str) -> None:
    """
    Handles the two-factor authentication process by sending and verifying the passcode.

    :param page: The Playwright page object.
    :param passcode: The passcode received for verification.
    """
    page.get_by_role("button", name="Send a passcode").click()
    page.get_by_role("textbox", name="Passcode").fill(passcode)
    page.get_by_test_id("verify-button").click()
    page.get_by_role("button", name="Yes, this is my device").click()


def navigate_to_compustat_data(page: Page) -> None:
    """
    Navigates to the Compustat North America Fundamentals Annual data page.

    :param page: The Playwright page object.
    """
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()
    page.get_by_role("link", name="Fundamentals Annual").click()


def search_for_company(page: Page, search_term: str) -> None:
    """
    Searches for a company by name or ticker using the provided search term.

    :param page: The Playwright page object.
    :param search_term: The company name or ticker to search for.
    """
    page.get_by_role("combobox", name="Search Name or Ticker").fill(search_term)
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")


def select_query_filters_and_submit(page: Page) -> None:
    """
    Selects the necessary query filters and submits the form.

    :param page: The Playwright page object.
    """
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Global Company Key (gvkey)").click()
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("CIK Number (cik)").click()
    with page.expect_popup() as page_info:
        page.get_by_role("button", name="Submit Form").click()
    page_info.value.close()


def run_workflow(playwright: Playwright) -> None:
    """
    Main function to run the complete Playwright workflow for WRDS login and data access.

    :param playwright: The Playwright instance.
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    navigate_to_login_page(page)
    perform_login(page, "whealy", "WRDS_password1")
    handle_two_factor_authentication(page, "1561471")
    navigate_to_compustat_data(page)
    search_for_company(page, "IBM")
    select_query_filters_and_submit(page)

    # Save session state
    context.storage_state(path="workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json")
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_workflow(playwright)
