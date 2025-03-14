import time
import re
from playwright.sync_api import Playwright, sync_playwright, Page


def navigate_to_data_source() -> str:
    """
    Navigate to the data retrieval tab and select Compustat Annual Fundamentals for North America.
    Returns the Python code to execute.
    """
    return '''
assert "wrds" in page.url, "Not on the WRDS page!"
page.get_by_role("tab", name=" Get Data ").click()
page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
page.get_by_role("link", name=" North America 19 child items").click()
page.get_by_role("link", name="Fundamentals Annual").click()
'''

def set_date_range(start_date: str, end_date: str) -> str:
    """
    Set the date range for data retrieval.
    Returns the Python code to execute.
    """
    return f'''
page.get_by_role("textbox", name="Start Date").fill("{start_date}")
page.get_by_role("textbox", name="End Date").fill("{end_date}")
'''

def enter_ticker(ticker: str) -> str:
    """
    Enter the company's ticker symbol.
    Returns the Python code to execute.
    """
    return f'''
combobox = page.get_by_role("combobox", name="Search Name or Ticker")
combobox.fill("{ticker}")
combobox.press("Enter")
'''

def add_variables(variables: list) -> str:
    """
    Add the desired variables to the analysis.
    Returns the Python code to execute.
    """
    variable_mapping = {
        "tic": "Ticker Symbol (tic)",
        "revt": "Revenue - Total (revt)",
        "dltt": "Long-Term Debt - Total (dltt)",
        "dt": "Total Debt Including Current",
        "dlc": "Debt in Current Liabilities"
    }
    
    code_parts = [
        'import time',
        f'variables = {variables}',
        'search_box = page.get_by_role("textbox", name="Search All")',
        'for variable in variables:',
        '    search_box.click()',
        '    search_box.fill(variable)',
        '    time.sleep(0.5)'
    ]
    
    # Add if-elif block for each variable
    for var in variable_mapping:
        if_stmt = f'    if variable == "{var}":'
        click_stmt = f'        page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9, [id^=\'select_all_container_div\']").get_by_text("{variable_mapping[var]}").click()'
        code_parts.extend([if_stmt, click_stmt])
    
    return '\n'.join(code_parts)

def set_output_options(email: str) -> str:
    """
    Set the output options for the data retrieval.
    Returns the Python code to execute.
    """
    return f'''
page.get_by_text("Excel spreadsheet (*.xlsx)").click()
email_box = page.get_by_role("textbox", name="E-Mail Address (Optional)")
email_box.fill("{email}")
'''

def perform_query_and_download() -> str:
    """
    Submit the form and download the result.
    Returns the Python code to execute.
    """
    return '''
with page.expect_popup() as page_info:
    page.get_by_role("button", name="Submit Form").click()
query_page = page_info.value

# Validate correct navigation
query_page.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9587217/")

with query_page.expect_download() as download_info:
    query_page.get_by_role("link", name="Download .xlsx Output").click()
download = download_info.value
'''