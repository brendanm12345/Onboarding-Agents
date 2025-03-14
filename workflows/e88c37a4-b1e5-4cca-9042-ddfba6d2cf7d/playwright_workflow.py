import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    page = context.new_page()
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="Compustat - Capital IQ", exact=True).click()
    page.get_by_role("link", name=" North America 19 child items").click()
    page.get_by_role("link", name="Fundamentals Annual").click()
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("UBER")
    page.get_by_role("combobox", name="Search Name or Ticker").press("Enter")
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").fill("2019-01")
    page.get_by_role("textbox", name="Start Date").press("Enter")
    page.get_by_role("textbox", name="End Date").click()
    page.get_by_role("textbox", name="End Date").press("ArrowLeft")
    page.get_by_role("textbox", name="End Date").press("ArrowLeft")
    page.get_by_role("textbox", name="End Date").press("ArrowLeft")
    page.get_by_role("textbox", name="End Date").fill("2024-03")
    page.get_by_role("textbox", name="End Date").press("ArrowRight")
    page.get_by_role("textbox", name="End Date").press("ArrowLeft")
    page.get_by_role("textbox", name="End Date").fill("2024-12")
    page.get_by_role("textbox", name="End Date").press("Enter")
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("tic")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Ticker Symbol (tic)").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("revt")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Revenue - Total (revt)").click()
    page.get_by_role("textbox", name="Search All").click()
    page.get_by_role("textbox", name="Search All").fill("debt")
    page.locator("#select_all_container_div-08689682-4bdf-3947-97d8-433f285f28a9").get_by_text("Long-Term Debt - Total (dltt)").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="Submit Form").click()
    page1 = page1_info.value
    page1.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9598543/")

    # ---------------------
    context.storage_state(path="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
