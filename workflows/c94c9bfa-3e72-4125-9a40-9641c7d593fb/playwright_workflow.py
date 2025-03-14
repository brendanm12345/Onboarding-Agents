import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    page = context.new_page()
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").fill("whealy")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("WRDS_password1")
    page.get_by_role("button", name="Login").click()
    page.goto("https://wrds-www.wharton.upenn.edu/")
    page.get_by_role("tab", name=" Get Data ").click()
    page.get_by_role("link", name="CRSP", exact=True).click()
    page.get_by_role("link", name=" Stock / Security Files 5").click()
    page.get_by_role("link", name="Monthly Stock File").click()
    page.get_by_role("textbox", name="Start Date").click()
    page.get_by_role("textbox", name="Start Date").fill("2022")
    page.get_by_role("textbox", name="Start Date").press("Enter")
    page.get_by_role("textbox", name="End Date").click()
    page.get_by_role("textbox", name="End Date").fill("2025")
    page.get_by_role("textbox", name="End Date").press("Enter")
    page.get_by_role("heading", name="Step 2: Apply your company").click()
    page.locator("div:nth-child(6) > .form-check").click()
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").click()
    page.get_by_role("combobox", name="Search Name or Ticker").fill("    * 7370 7371 7372 7373 7374 7375 7376 7377 7378 7379")
    page.locator("#save_codes").check()
    page.get_by_role("textbox", name="Code List Name").click()
    page.get_by_role("textbox", name="Code List Name").fill("tech1")
    page.get_by_role("button", name=" All").click()
    page.get_by_text("Excel spreadsheet (*.xlsx)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").click()
    page.get_by_role("textbox", name="E-Mail Address (Optional)").fill("mclaughlin@stanford.edu")
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="Submit Form").click()
    page1 = page1_info.value
    page1.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9601393/")
    page1.get_by_role("link", name="Rerun").click()
    with page1.expect_popup() as page2_info:
        page1.get_by_role("button", name="Submit Form").click()
    page2 = page2_info.value
    page2.goto("https://wrds-www.wharton.upenn.edu/query-manager/query/9601394/")

    # ---------------------
    context.storage_state(path="/Users/brendanmclaughlin/Documents/code/research/onboarding-agents/onboarding-agents/auth/auth.json")
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
