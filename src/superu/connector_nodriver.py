import time
import json
import asyncio
import nodriver
from nodriver.core import tab
from pathlib import Path
from logging import getLogger, StreamHandler
from logging import INFO


class BrowserNodriver:
    def __init__(self):
        self.cookies_file = Path("src/cookies/superu.dat")
        self.superu_logger = getLogger(__name__)
        self.superu_logger.setLevel(INFO)
        self.superu_logger.addHandler(StreamHandler())

    def get_page(
        self, url: str, headless: bool = False, need_scroll_down=False
    ) -> str:
        self.superu_logger.info(f"Getting page: {url}")
        return asyncio.run(self._get_page_async(url, headless, need_scroll_down))

    async def _get_page_async(
        self, url: str, headless: bool = False, need_scroll_down=False
    ) -> str:
        """Fetches the HTML content of a page using Playwright.
        Args:
            url (str): The URL of the page to fetch.
            headless (bool): Whether to run the browser in headless mode. Defaults to True.
            need_scroll_down (bool): Whether to scroll down the page to load all content. Defaults to False.
        Returns:
            str: A list of HTML content strings for each page.
        """
        try:
            browser = await nodriver.start(headless=headless)

            # we need to load cookies from file to indicate geolocation and avoid being blocked
            # price are indicated by geolocation
            await browser.cookies.load(self.cookies_file)
            await asyncio.sleep(5)
            page: tab.Tab = await browser.get(url)
            await asyncio.sleep(10)

            # after scrap we store new cookies
            await browser.cookies.save(self.cookies_file)
            content = await page.get_content()
            await page.close()
            return content
            # with open("page.html", "r", encoding="utf-8") as f:
            #     content = f.read()
            # return content
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to load cookies: {e}")
        except FileNotFoundError:
            print("Cookie file does not exist.")
        except Exception as e:
            self.superu_logger.error(f"Error getting page: {e}")
            return []

    def slow_scroll_down(self, page: tab.Tab) -> None:
        """Scrolls down the page slowly to allow content to load.
        Needed in Lidl's website to load all products.
        Args:
            page: The Playwright page object.
        Returns:
            None
        """
        try:
            self.superu_logger.info("Scrolling down the page to load all content...")
            # Get total page height
            scroll_height = page.evaluate("() => document.body.scrollHeight")

            # Scroll in steps
            step_size = 500  # pixels per step
            pause = 0.3  # seconds to wait between steps

            for position in range(0, scroll_height, step_size):
                page.evaluate(f"window.scrollTo(0, {position})")
                time.sleep(pause)  # Let content load
        except Exception as e:
            self.superu_logger.error(f"Error scrolling down the page: {e}")
            return
    
    def request(self, url: str, method: str, headers: dict = {}, data: dict = {}) -> str:
        raise NotImplementedError()