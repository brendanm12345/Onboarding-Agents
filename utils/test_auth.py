from playwright.sync_api import sync_playwright

def run_with_auth_state(auth_json_path, url):
    """
    Run a Playwright session using a saved authentication state.
    
    Args:
        auth_json_path: Path to the auth.json file
        url: URL to navigate to with the authenticated state
    """
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state=auth_json_path)
        page = context.new_page()
        page.goto(url)
        print(f"Successfully loaded authenticated session for {url}")
        input("Press Enter to close the browser...")
        context.close()
        browser.close()

if __name__ == "__main__":
    # Path to saved auth.json file
    auth_file = "src/scripts/workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json"
    
    # URL that requires auth
    target_url = "https://wrds-www.wharton.upenn.edu/"
    
    run_with_auth_state(auth_file, target_url)