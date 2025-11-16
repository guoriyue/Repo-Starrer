"""
GitHub Repository Auto-Star Automation Script

This script automates the process of starring multiple repositories on a GitHub
user's profile page. It navigates to the repositories tab and stars each repository
by clicking on the star buttons and submitting the forms.

The script uses Playwright to interact with the GitHub website and properly handles
dynamic content loading and form submissions.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


async def star_user_repositories(
    url: str = "https://github.com/karpathy?tab=repositories",
    storage_state: Optional[str] = None,
    headless: bool = True,
    user_data_dir: Optional[str] = None,
) -> None:
    """
    Automate starring repositories on a GitHub user's profile.

    This function opens a GitHub user's repositories page, scrolls through the list,
    and stars each visible repository by clicking the star button and submitting
    the star form.

    Args:
        url: The GitHub repositories URL to navigate to
        storage_state: Path to a JSON file containing browser storage state (cookies, local storage, etc.)
                      This allows the script to run as an authenticated user
        headless: Whether to run the browser in headless mode (default: True)
        user_data_dir: Path to Chrome user data directory to use existing profile
                       (e.g., "~/Library/Application Support/Google/Chrome/Default" on macOS)

    Raises:
        Exception: If there are issues with navigation or form submission
    """

    print("Starting playwright...")
    async with async_playwright() as playwright:
        # If user_data_dir is provided, use persistent context with existing profile
        if user_data_dir:
            print(f"Launching Chrome with profile: {user_data_dir}")
            user_data_path = Path(user_data_dir).expanduser()
            print(f"Expanded path: {user_data_path}")
            print("This may take a while if Chrome needs to initialize the profile...")
            context: BrowserContext = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_path),
                headless=headless,
                viewport={"width": 1508, "height": 859},
                channel="chrome",  # Use actual Chrome instead of Chromium
            )
            print("Chrome launched!")
            page: Page = context.pages[0] if context.pages else await context.new_page()
            print(f"Got page, current pages count: {len(context.pages)}")
        else:
            print("Launching browser with default settings...")
            # Launch browser with optional storage state
            browser: Browser = await playwright.chromium.launch(headless=headless)

            # Create context with optional storage state for authentication
            context_kwargs = {"viewport": {"width": 1508, "height": 859}}
            if storage_state and Path(storage_state).exists():
                context_kwargs["storage_state"] = storage_state

            context: BrowserContext = await browser.new_context(**context_kwargs)
            page: Page = await context.new_page()
            print("Browser launched!")

        try:
            # Navigate to the repositories page
            print(f"Navigating to {url}")
            print(f"Current URL before navigation: {page.url}")

            # Force navigation with longer timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"Navigation completed. Current URL: {page.url}")

            # Just wait a bit for dynamic content to load (no need for networkidle)
            await page.wait_for_timeout(3000)
            print(f"Page ready. Final URL: {page.url}")

            # Wait for the repository list to be visible
            await page.wait_for_selector("#user-repositories-list", timeout=1000000)

            # Get all repository items from the list
            repo_items = await page.query_selector_all("#user-repositories-list li")
            total_repos = len(repo_items)
            print(f"Found {total_repos} repositories on the page")

            # Counter for successfully starred repos
            starred_count = 0

            # Iterate through each repository and star it
            for index in range(1, total_repos + 1):
                try:
                    # Find the star form for this repository
                    # The XPath pattern: //div[@id='user-repositories-list']/ul/li[{index}]/div[2]/div[1]/div[2]/form
                    star_form_selector = (
                        f"#user-repositories-list li:nth-child({index}) "
                        "div.col-2 div:first-child div:last-child form"
                    )

                    # Try to find the form using XPath as a fallback
                    star_form = await page.query_selector(
                        f"//div[@id='user-repositories-list']/ul/li[{index}]/div[2]/div[1]/div[2]/form"
                    )

                    if star_form:
                        # Find the button inside the form instead of submitting the form
                        star_button = await star_form.query_selector("button[type='submit']")

                        if star_button:
                            # Scroll the button into view to ensure it's clickable
                            await star_button.scroll_into_view_if_needed()
                            await page.wait_for_timeout(200)

                            print(f"Starring repository {index}/{total_repos}")
                            # Click the button (GitHub uses AJAX, won't reload page)
                            await star_button.click()

                            # Wait for the AJAX response
                            await page.wait_for_timeout(800)
                            starred_count += 1
                            print(f"✓ Starred {index}/{total_repos}")

                            # Brief delay between submissions to avoid rate limiting
                            await page.wait_for_timeout(300)
                    else:
                        # If form not found, try clicking the star button directly
                        star_button_selector = (
                            f"#user-repositories-list li:nth-child({index}) "
                            "button[aria-label*='Star']"
                        )
                        star_button = await page.query_selector(star_button_selector)

                        if star_button:
                            await star_button.scroll_into_view_if_needed()
                            await star_button.click()
                            await page.wait_for_timeout(800)
                            starred_count += 1
                            print(f"✓ Starred repository {index}/{total_repos}")

                except Exception as e:
                    print(f"Error starring repository {index}: {str(e)}")
                    continue

            print(f"\nAutomation complete! Successfully starred {starred_count}/{total_repos} repositories")

        except Exception as e:
            print(f"Error during automation: {str(e)}")
            raise

        finally:
            # Clean up
            await context.close()
            if not user_data_dir:
                await browser.close()


async def main() -> None:
    """
    Main entry point for the automation script.

    Uses a Playwright-managed profile to persist login credentials.
    First run: Browser opens, log into GitHub manually
    Future runs: Automatically logged in
    """
    PROFILE = Path.home() / "Library/Application Support/pw-profiles/github.com"
    PROFILE.mkdir(parents=True, exist_ok=True)

    await star_user_repositories(
        url="https://github.com/karpathy?tab=repositories",
        user_data_dir=str(PROFILE),
        headless=False
    )


if __name__ == "__main__":
    # Run the automation
    asyncio.run(main())
