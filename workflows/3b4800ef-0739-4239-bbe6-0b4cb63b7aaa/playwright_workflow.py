import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").fill("whealy")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("WRDS_password1")
    page.get_by_role("button", name="Login").click()
    page.get_by_role("button", name="Send a passcode").click()
    page.get_by_role("textbox", name="Passcode").fill("1561471")
    page.get_by_test_id("verify-button").click()
    page.get_by_role("button", name="Yes, this is my device").click()
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()
    page.get_by_role("link", name="Fundamentals Annual").click()
    page.goto("https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/")
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("")
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Code Lookup: Compustat North").click()
    page1 = page1_info.value
    page1.close()
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("IBM")
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Global Company Key (gvkey)").click()
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("CIK Number (cik)").click()
    with page.expect_popup() as page2_info:
        page.get_by_role("button", name="Submit Form").click()
    page2 = page2_info.value
    page2.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9587098/")
    page2.close()
    page.close()

    # ---------------------
    context.storage_state(path="workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
