import re
from playwright.sync_api import Playwright, sync_playwright, Browser, Page


def navigate_to_crsp(page: Page) -> None:
    """
    Navigates to the CRSP section in the WRDS platform.
    """
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="CRSP", exact=True).click()


def select_stock_security_files(page: Page) -> None:
    """
    Navigates to the Stock / Security Files and selects Monthly Stock File.
    """
    page.get_by_role("link", name=" Stock / Security Files 5").click()
    page.get_by_role("link", name="Monthly Stock File").click()


def set_date_range(page: Page, start_date: str, end_date: str) -> None:
    """
    Sets the date range for the data.

    :param start_date: The start date in YYYY format.
    :param end_date: The end date in YYYY format.
    """
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").fill(start_date)
    page.get_by_role("textbox", name="Start Date").press("Enter")
    page.get_by_role("textbox", name="End Date").click()
    page.get_by_role("textbox", name="End Date").fill(end_date)
    page.get_by_role("textbox", name="End Date").press("Enter")


def enter_sic_codes(page: Page, codes: str, code_name: str) -> None:
    """
    Enters SIC codes and saves them under a specified list name.

    :param codes: A string containing SIC codes separated by spaces.
    :param code_name: The name to save the SIC codes under.
    """
    page.get_by_role("heading", name="Step 2: Apply your company").click()
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill(codes)
    page.locator("#save_codes").check()
    page.get_by_role("textbox", name="Code List Name").click()
    page.get_by_role("textbox", name="Code List Name").fill(code_name)


def add_all_variables(page: Page) -> None:
    """
    Selects all available query variables.
    """
    page.get_by_role("button", name=" All").click()


def set_output_options(page: Page, email: str) -> None:
    """
    Sets output options including the email address for report delivery.

    :param email: The email address to send the report to.
    """
    page.get_by_text("Excel spreadsheet (*.xlsx)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").fill(email)


def perform_query_and_download(page: Page) -> Page:
    """
    Submits the query form and handles the popup for query running status.

    :returns: The page showing the query running status.
    """
    with page.expect_popup() as popup_info:
        page.get_by_role("button", name="Submit Form").click()
    queried_page = popup_info.value
    return queried_page


def rerun_query(page: Page) -> Page:
    """
    Rerun the query if there was an error.

    :returns: The page after rerunning the query.
    """
    page.get_by_role("link", name="Rerun").click()
    with page.expect_popup() as popup_info:
        page.get_by_role("button", name="Submit Form").click()
    return popup_info.value


def main_workflow(playwright: Playwright) -> None:
    """
    Main workflow for interacting with the WRDS platform to gather financial data.
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="auth/auth.json")
    page = context.new_page()
    
    print(f"Current URL before executing navigate_to_crsp: {page.url}")
    navigate_to_crsp(page)
    print(f"Current URL before executing select_stock_security_files: {page.url}")
    select_stock_security_files(page)
    print(f"Current URL before executing set_date_range: {page.url}")
    set_date_range(page, "2022", "2025")
    print(f"Current URL before executing enter_sic_codes: {page.url}")
    enter_sic_codes(page, "    * 7370 7371 7372 7373 7374 7375 7376 7377 7378 7379", "tech1")
    print(f"Current URL before executing add_all_variables: {page.url}")
    add_all_variables(page)
    print(f"Current URL before executing set_output_options: {page.url}")
    set_output_options(page, "mclaughlin@stanford.edu")
    print(f"Current URL before executing perform_query_and_download: {page.url}")
    query_page = perform_query_and_download(page)
    print(f"Current URL before executing rerun_query: {query_page.url}")
    rerun_query(query_page)

    context.close()
    browser.close()


with sync_playwright() as playwright:
    main_workflow(playwright)
