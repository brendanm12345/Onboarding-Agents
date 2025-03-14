import time
import re
from playwright.sync_api import Playwright, sync_playwright, Page


def open_page(context, url: str) -> Page:
    """
    Open a new page in the browser with the given URL.

    :param context: The browser context to open the page in.
    :param url: The URL to navigate to.
    :return: A reference to the page object.
    """
    page = context.new_page()
    page.goto(url)
    return page


def navigate_to_data_source(page: Page) -> None:
    """
    Navigate to the data retrieval tab and select Compustat Annual Fundamentals for North America.

    :param page: The page object to perform actions on.
    """
    assert "wrds" in page.url, "Not on the WRDS page!"
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()
    page.get_by_role("link", name="Fundamentals Annual").click()


def set_date_range(page: Page, start_date: str, end_date: str) -> None:
    """
    Set the date range for data retrieval.

    :param page: The page object to perform actions on.
    :param start_date: The start date in YYYY-MM format.
    :param end_date: The end date in YYYY-MM format.
    """
    page.get_by_role("textbox", name="Start Date").fill(start_date)
    page.get_by_role("textbox", name="End Date").fill(end_date)


def enter_ticker(page: Page, ticker: str) -> None:
    """
    Enter the company's ticker symbol.

    :param page: The page object to perform actions on.
    :param ticker: The ticker symbol for the company.
    """
    combobox = page.get_by_role("combobox", name="Search Name or Ticker")
    combobox.fill(ticker)
    combobox.press("Enter")


def add_variables(page: Page, variables: list) -> None:
    """
    Add the desired variables to the analysis. Only supports "tic", "revt", "dltt", "dt", "dlc" right now

    :param page: The page object to perform actions on.
    :param variables: A list of variables to select.
    """
    search_box = page.get_by_role("textbox", name="Search All")
    
    for variable in variables:
        # Clear any existing text, fill with the variable name
        search_box.click()
        search_box.fill(variable)
        
        # Find and click the variable in the dropdown
        # The selector may need adjustment based on the actual page structure
        # Wait a moment for the dropdown to populate
        time.sleep(0.5)
        
        # Using a more specific selector based on your working approach
        if variable == "tic":
            page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^='select_all_container_div']").get_by_text("Ticker Symbol (tic)").click()
        elif variable == "revt":
            page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^='select_all_container_div']").get_by_text("Revenue - Total (revt)").click()
        elif variable == "dltt":
            page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^='select_all_container_div']").get_by_text("Long-Term Debt - Total (dltt)").click()
        elif variable == "dt":
            page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^='select_all_container_div']").get_by_text("Total Debt Including Current").click()
        elif variable == "dlc":
            page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^='select_all_container_div']").get_by_text("Debt in Current Liabilities").click()



def set_output_options(page: Page, email: str) -> None:
    """
    Set the output options for the data retrieval, including the format and email.

    :param page: The page object to perform actions on.
    :param email: The email address to send the report to.
    """
    page.get_by_text("Excel spreadsheet (*.xlsx)").click()
    email_box = page.get_by_role("textbox", name="E-Mail Address (Optional)")
    email_box.fill(email)


def perform_query_and_download(page: Page) -> None:
    """
    Submit the form, wait for the query to complete, and download the result.

    :param page: The page object to perform actions on.
    """
    with page.expect_popup() as page_info:
        page.get_by_role("button", name="Submit Form").click()
    query_page = page_info.value
    
    # Validate correct navigation
    query_page.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9587217/")

    with query_page.expect_download() as download_info:
        query_page.get_by_role("link", name="Download .xlsx Output").click()
    download = download_info.value
    # Download path could be used here if needed:
    # download.save_as(<desired_path>)


def main_workflow() -> None:
    """
    Main workflow to automate the process of downloading Microsoft data from WRDS.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="src/scripts/workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json")

        try:
            page = open_page(context, "https://wrds-www.wharton.upenn.edu/")
            navigate_to_data_source(page)
            set_date_range(page, "2020-01", "2024-12")
            enter_ticker(page, "MSFT")
            add_variables(page, ["tic", "revt", "dltt", "dt", "dlc"])
            set_output_options(page, "mclaughlin@stanford.edu")
            perform_query_and_download(page)
        finally:
            context.storage_state(path="src/scripts/workflows/f821e2ca-a8a7-47fd-9379-c9bdf4c9ca8d/auth.json")
            context.close()
            browser.close()


# Run the main workflow
if __name__ == "__main__":
    main_workflow()
