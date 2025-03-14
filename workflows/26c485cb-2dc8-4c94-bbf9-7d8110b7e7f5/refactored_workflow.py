from playwright.sync_api import Playwright, sync_playwright, Page, expect


def navigate_to_kaggle_homepage(page: Page, homepage_url: str) -> None:
    """
    Navigates to the Kaggle homepage.

    This corresponds to the speech transcript step where the user starts at the Kaggle homepage.

    :param page: The Playwright Page object.
    :param homepage_url: The URL of the Kaggle homepage.
    """
    assert page is not None, "Page object must not be None"
    page.goto(homepage_url)


def click_on_onboarded_agent(page: Page) -> None:
    """
    Clicks on the button labeled 'OnboardedAgent'.

    This step is part of the workflow for accessing the user's work on Kaggle.

    :param page: The Playwright Page object.
    """
    assert page is not None, "Page object must not be None"
    page.get_by_role("button", name="OnboardedAgent").click()


def click_on_your_work(page: Page) -> None:
    """
    Navigates to the 'Your Work' section by clicking the corresponding link.

    This corresponds to the transcript where the user goes to the profile and clicks on their work.

    :param page: The Playwright Page object.
    """
    assert page is not None, "Page object must not be None"
    page.get_by_role("link", name="Your Work").click()


def search_for_notebook(page: Page, search_text: str) -> None:
    """
    Searches for a notebook in the 'Your Work' section using the given search text.

    This corresponds to the speech section where the user demonstrates searching for a notebook.

    :param page: The Playwright Page object.
    :param search_text: The text to search for in the notebook list.
    """
    assert page is not None, "Page object must not be None"
    search_box = page.get_by_role("textbox", name="Search Your Work")
    search_box.click()
    search_box.fill(search_text)
    # Simulate selection clearing as in the original demonstration
    search_box.press("ControlOrMeta+Shift+ArrowLeft")
    search_box.press("ArrowRight")
    search_box.fill("")


def click_on_notebook(page: Page, notebook_name: str) -> None:
    """
    Clicks on a notebook from the search results based on the provided notebook name.

    This matches the demonstration where the specific notebook is clicked to load its content.

    :param page: The Playwright Page object.
    :param notebook_name: The accessible name of the notebook link to click.
    """
    assert page is not None, "Page object must not be None"
    page.locator("#site-content").get_by_role("link", name=notebook_name).click()


def main_workflow() -> None:
    """
    Executes the entire workflow to navigate Kaggle, view past work, search for a notebook, and open it.

    Uses atomic actions derived from the demonstration transcript.
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
