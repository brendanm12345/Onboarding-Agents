import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json")
    page = context.new_page()
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()
    page.get_by_role("link", name="Fundamentals Annual").click()
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").fill("2010-01")
    page.get_by_role("textbox", name="End Date").click()
    page.get_by_role("textbox", name="End Date").fill("2024-12")
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").press("ArrowLeft")
    page.get_by_role("textbox", name="Start Date").press("ArrowRight")
    page.get_by_role("textbox", name="Start Date").fill("2020-01")
    page.get_by_role("textbox", name="Start Date").press("Enter")
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("MFST")
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")
    page.get_by_role("link", name="×").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("MSFT")
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("tic")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Ticker Symbol (tic)").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("revt")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Revenue - Total (revt)").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("dltt")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Long-Term Debt - Total (dltt)").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("dt")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Total Debt Including Current").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("dlc")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Debt in Current Liabilities").click()
    page.get_by_text("Excel spreadsheet (*.xlsx)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").fill("mclaughlin@stanford.edu")
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="Submit Form").click()
    page1 = page1_info.value
    page1.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9587217/")
    with page1.expect_download() as download_info:
        with page1.expect_popup() as page2_info:
            page1.get_by_role("link", name="Download .xlsx Output").click()
        page2 = page2_info.value
    download = download_info.value
    page2.close()
    page1.close()
    page.close()

    # ---------------------
    context.storage_state(path="workflows/f821e2ca-a8a7-47fd-9379-c9bdf4c9ca8d/auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
