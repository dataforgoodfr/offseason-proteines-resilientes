import time
import json
import asyncio
import nodriver
from nodriver.core import tab
from pathlib import Path
from logging import getLogger, StreamHandler
from logging import INFO


class ConnectorNodriver:
    def __init__(self):
        self.cookies_file = self.__get_cookies_file()
        
        self.nodriver_logger = getLogger(__name__)
        self.nodriver_logger.setLevel(INFO)
        self.nodriver_logger.addHandler(StreamHandler())

    def __get_cookies_file(self) -> Path:
        script_dir = Path(__file__).parent
        cookies_dir = script_dir / "cookies"
        cookies_dir.mkdir(exist_ok=True)
        return cookies_dir / "superu.dat"
    
    async def get_page(
        self, url: str, headless: bool = False
    ) -> str:
        self.nodriver_logger.info(f"Getting page: {url}")
        return await self._get_page_async(url, headless)

    async def _get_page_async(
        self, url: str, headless: bool = False
    ) -> str:
        """Fetches the HTML content of a page using Playwright.
        Args:
            url (str): The URL of the page to fetch.
            headless (bool): Whether to run the browser in headless mode. Defaults to True.
        Returns:
            str: A list of HTML content strings for each page.
        """
        try:
            browser = await nodriver.start(headless=headless)
            await self._load_cookies(browser)
            content = await self._scrape_page(browser, url)
            await self._save_cookies(browser)
            
            return content
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to load cookies: {e}")
        except FileNotFoundError:
            print("Cookie file does not exist.")
        except Exception as e:
            self.nodriver_logger.error(f"Error getting page: {e}")
            return []

    async def _load_cookies(self, browser) -> None:
        """Load cookies from the file to indicate the geolocation and avoid being blocked.
        The prices are indicated by geolocation.
        Args:
            browser: The nodriver browser instance.
        """
        self.nodriver_logger.info(f"Checking for cookies file: {self.cookies_file}")
        if self.cookies_file.exists():
            self.nodriver_logger.info(f"Loading cookies from: {self.cookies_file}")
            try:
                await browser.cookies.load(self.cookies_file)
                self.nodriver_logger.info("Cookies loaded successfully")
            except Exception as e:
                self.nodriver_logger.error(f"Failed to load cookies: {e}")
        else:
            self.nodriver_logger.warning(f"Cookies file not found: {self.cookies_file}")

    async def _scrape_page(self, browser, url: str) -> str:
        """Scrape the web page.
        Args:
            browser: The nodriver browser instance.
            url (str): The URL of the page to scrape.
        Returns:
            str: The HTML content of the page.
        """
        await asyncio.sleep(5)
        page: tab.Tab = await browser.get(url)
        await asyncio.sleep(10)

        content = await page.get_content()
        await page.close()
        return content

    async def _save_cookies(self, browser) -> None:
        """Save cookies after scraping.
        Args:
            browser: The nodriver browser instance.
        """
        try:
            await browser.cookies.save(self.cookies_file)
            self.nodriver_logger.info(f"Cookies saved to: {self.cookies_file}")
        except Exception as e:
            self.nodriver_logger.error(f"Failed to save cookies: {e}")

    