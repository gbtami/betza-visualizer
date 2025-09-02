from playwright.sync_api import sync_playwright, Page, expect

def verify_catalog():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the local server
        page.goto("http://localhost:8080")

        # Find the Amazon piece and wait for it to be visible
        amazon_locator = page.locator(".piece-catalog-item", has_text="Amazon")
        expect(amazon_locator).to_be_visible(timeout=10000)

        # Click the Amazon piece
        amazon_locator.click()

        # Assert that the input field has the correct Betza string
        expect(page.locator("#betzaInput")).to_have_value("QN")

        # Take a screenshot
        page.screenshot(path="jules-scratch/verification/verification.png")

        browser.close()

if __name__ == "__main__":
    verify_catalog()
