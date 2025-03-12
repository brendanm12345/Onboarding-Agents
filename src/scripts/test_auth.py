from playwright.sync_api import sync_playwright

def run_with_auth_state(auth_json_path, url):
    """
    Run a Playwright session using a saved authentication state.
    
    Args:
        auth_json_path: Path to the auth.json file
        url: URL to navigate to with the authenticated state
    """
    with sync_playwright() as playwright:
        # Launch browser
        browser = playwright.chromium.launch(headless=False)
        
        # Create a new context with the saved storage state
        context = browser.new_context(storage_state=auth_json_path)
        
        # Create a new page in the authenticated context
        page = context.new_page()
        
        # Navigate to the URL - you should already be authenticated
        page.goto(url)
        
        # Perform your operations on the authenticated page
        print(f"Successfully loaded authenticated session for {url}")
        
        # For demonstration, let's wait for user to see it worked
        input("Press Enter to close the browser...")
        
        # Close everything
        context.close()
        browser.close()

# Example usage
if __name__ == "__main__":
    # Path to your saved auth.json file
    auth_file = "workflows/3b4800ef-0739-4239-bbe6-0b4cb63b7aaa/auth.json"
    
    # URL that requires authentication
    target_url = "https://wrds-www.wharton.upenn.edu/"
    
    run_with_auth_state(auth_file, target_url)