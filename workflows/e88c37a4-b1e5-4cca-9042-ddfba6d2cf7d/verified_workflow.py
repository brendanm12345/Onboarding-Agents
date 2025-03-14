# WORKING - basic company revenue and debt analysis

from playwright.sync_api import Playwright, sync_playwright, Page, expect


def navigate_to_data_source(page: Page) -> None:
    """
    Navigate to the data source home page and open the Get Data tab.
    """
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("tab", name=" Get Data ").click()


def select_compustat_data(page: Page) -> None:
    """
    Click on the link to Compustat - Capital IQ and navigate to North America data.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()


def select_fundamentals_annual(page: Page) -> None:
    """
    Navigate to and select the Fundamentals Annual data set.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/")
    page.get_by_role("link", name="Fundamentals Annual").click()


def enter_ticker(page: Page, ticker: str) -> None:
    """
    Enter the specified ticker into the Search Name or Ticker combobox.

    Args:
        page (Page): The Playwright page object to interact with the browser.
        ticker (str): The ticker symbol to be entered.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/")
    assert ticker.isupper(), "Ticker should be in uppercase format."
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill(ticker)
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")


def set_date_range(page: Page, start_date: str, end_date: str) -> None:
    """
    Set the date range for the query, including start and end dates.

    Args:
        page (Page): The Playwright page object to interact with the browser.
        start_date (str): The start date in YYYY-MM format.
        end_date (str): The end date in YYYY-MM format.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/")
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").fill(start_date)
    page.get_by_role("textbox", name="End Date").click()
    page.get_by_role("textbox", name="End Date").fill(end_date)


def add_variables(page: Page, variables: list) -> None:
    """
    Add the specified variables to the query.

    Args:
        page (Page): The Playwright page object to interact with the browser.
        variables (list): A list of variable names to be added.
    """
    expect(page).to_have_url("https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/")
    variable_map = {
        "tic": "Ticker Symbol (tic)",
        "revt": "Revenue - Total (revt)",
        "dltt": "Long-Term Debt - Total (dltt)"
    }
    
    for variable in variables:
        page.get_by_role("textbox", name="Search All").click()
        # Use the search terms from the original script if available
        search_term = variable
        if variable == "dltt":
            search_term = "debt"
            
        page.get_by_role("textbox", name="Search All").fill(search_term)
        page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text(variable_map[variable]).click()


def perform_query_and_download(page: Page) -> None:
    """
    Submit the query form and handle the resulting popup.
    """
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="Submit Form").click()
    page1 = page1_info.value
    # Additional handling if needed


def main_workflow() -> None:
    """
    Main function to execute the automated workflow using Playwright.
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="auth/auth.json")
        page = context.new_page()

        print(f"Current URL before executing navigate_to_data_source: {page.url}")
        navigate_to_data_source(page)

        print(f"Current URL before executing select_compustat_data: {page.url}")
        select_compustat_data(page)

        print(f"Current URL before executing select_fundamentals_annual: {page.url}")
        select_fundamentals_annual(page)

        print(f"Current URL before executing enter_ticker: {page.url}")
        enter_ticker(page, "UBER")

        print(f"Current URL before executing set_date_range: {page.url}")
        set_date_range(page, "2019-01", "2024-12")

        print(f"Current URL before executing add_variables: {page.url}")
        add_variables(page, ["tic", "revt", "dltt"])

        print(f"Current URL before executing perform_query_and_download: {page.url}")
        perform_query_and_download(page)

        context.close()
        browser.close()


if __name__ == "__main__":
    main_workflow()
