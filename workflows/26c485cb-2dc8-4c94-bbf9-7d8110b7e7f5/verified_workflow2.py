# WORKS - basic kaggle view past work and click notebook workflow

from playwright.sync_api import Playwright, sync_playwright, Page, expect


def navigate_to_kaggle_homepage(page: Page, homepage_url: str) -> None:
    """
    Navigates to the Kaggle homepage.

    Before navigating, asserts that the current URL is 'about:blank' (initial state).

    :param page: The Playwright Page object.
    :param homepage_url: The URL of the Kaggle homepage.
    """
    # Assert precondition: the page should be about:blank
    expect(page).to_have_url('about:blank')
    page.goto(homepage_url)


def click_on_onboarded_agent(page: Page) -> None:
    """
    Clicks on the button labeled 'OnboardedAgent'.

    Before clicking, asserts that the current URL is 'https://www.kaggle.com/' as expected.

    :param page: The Playwright Page object.
    """
    # Assert precondition: user is at Kaggle homepage
    expect(page).to_have_url('https://www.kaggle.com/')
    page.get_by_role("button", name="OnboardedAgent").click()


def click_on_your_work(page: Page) -> None:
    """
    Navigates to the 'Your Work' section by clicking the corresponding link.

    Asserts that the user is on the Kaggle homepage before clicking, then waits for the URL to change to 'https://www.kaggle.com/work' after clicking.

    :param page: The Playwright Page object.
    """
    # Assert precondition: user should be on Kaggle homepage before clicking
    expect(page).to_have_url('https://www.kaggle.com/')
    page.get_by_role("link", name="Your Work").click()
    # Instead of a generic network idle wait, wait explicitly for the URL change
    page.wait_for_url("https://www.kaggle.com/work")


def search_for_notebook(page: Page, search_text: str) -> None:
    """
    Searches for a notebook in the 'Your Work' section using the provided search text.

    Before executing, asserts that the current URL is 'https://www.kaggle.com/work'.

    :param page: The Playwright Page object.
    :param search_text: The text to search for in the notebook list.
    """
    # Assert precondition: the current URL should be the 'Your Work' section
    expect(page).to_have_url('https://www.kaggle.com/work')
    search_box = page.get_by_role("textbox", name="Search Your Work")
    search_box.click()
    search_box.fill(search_text)
    # Simulating the clearing action as per the original demonstration
    search_box.press("ControlOrMeta+Shift+ArrowLeft")
    search_box.press("ArrowRight")
    search_box.fill("")


def click_on_notebook(page: Page, notebook_name: str) -> None:
    """
    Clicks on a notebook from the search results based on the provided notebook name.

    Asserts that the current URL is 'https://www.kaggle.com/work' before executing.

    :param page: The Playwright Page object.
    :param notebook_name: The accessible name of the notebook link to click.
    """
    # Assert precondition: still in the 'Your Work' section
    expect(page).to_have_url('https://www.kaggle.com/work')
    page.locator("#site-content").get_by_role("link", name=notebook_name).click()


def main_workflow() -> None:
    """
    Executes the complete workflow:
    - Navigate to Kaggle homepage
    - Click the 'OnboardedAgent' button
    - Navigate to the 'Your Work' section
    - Search for a notebook
    - Click on the selected notebook

    This function sequences atomic actions and validates the URL state before each operation.
    """
    with sync_playwright() as playwright:
        # Launch the browser with saved authentication state
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="auth/auth.json")
        page = context.new_page()

        # Step 1: Navigate to Kaggle homepage
        print(f"Current URL before executing navigate_to_kaggle_homepage: {page.url}")
        navigate_to_kaggle_homepage(page, "https://www.kaggle.com/")

        # Step 2: Click on the OnboardedAgent button
        print(f"Current URL before executing click_on_onboarded_agent: {page.url}")
        click_on_onboarded_agent(page)

        # Step 3: Navigate to 'Your Work'
        print(f"Current URL before executing click_on_your_work: {page.url}")
        click_on_your_work(page)

        # Step 4: Search for a specific notebook
        print(f"Current URL before executing search_for_notebook: {page.url}")
        search_for_notebook(page, "my last notebook")

        # Step 5: Click on the notebook result
        print(f"Current URL before executing click_on_notebook: {page.url}")
        click_on_notebook(page, "notebookf66c1ad69f")

        # Save storage state and cleanup
        context.storage_state(path="auth/auth.json")
        context.close()
        browser.close()


if __name__ == "__main__":
    main_workflow()
