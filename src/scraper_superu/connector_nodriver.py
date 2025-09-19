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
        self, url: str, headless: bool = False, need_scroll_down=False
    ) -> str:
        self.nodriver_logger.info(f"Getting page: {url}")
        return await self._get_page_async(url, headless, need_scroll_down)

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
            
            # Gestion des cookies
            await self._load_cookies(browser)
            
            # Scraping de la page
            content = await self._scrape_page(browser, url, need_scroll_down)
            
            # Sauvegarde des cookies après le scraping
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
        """Charge les cookies depuis le fichier pour indiquer la géolocalisation et éviter d'être bloqué.
        Les prix sont indiqués par géolocalisation.
        Args:
            browser: L'instance du navigateur nodriver.
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

    async def _scrape_page(self, browser, url: str, need_scroll_down: bool = False) -> str:
        """Effectue le scraping de la page web.
        Args:
            browser: L'instance du navigateur nodriver.
            url (str): L'URL de la page à scraper.
            need_scroll_down (bool): Si True, fait défiler la page pour charger tout le contenu.
        Returns:
            str: Le contenu HTML de la page.
        """
        await asyncio.sleep(5)
        page: tab.Tab = await browser.get(url)
        await asyncio.sleep(10)

        if need_scroll_down:
            self.slow_scroll_down(page)

        content = await page.get_content()
        await page.close()
        return content

    async def _save_cookies(self, browser) -> None:
        """Sauvegarde les cookies après le scraping.
        Args:
            browser: L'instance du navigateur nodriver.
        """
        try:
            await browser.cookies.save(self.cookies_file)
            self.nodriver_logger.info(f"Cookies saved to: {self.cookies_file}")
        except Exception as e:
            self.nodriver_logger.error(f"Failed to save cookies: {e}")

    # def slow_scroll_down(self, page: tab.Tab) -> None:
    #     """Scrolls down the page slowly to allow content to load.
    #     Needed in Lidl's website to load all products.
    #     Args:
    #         page: The Playwright page object.
    #     Returns:
    #         None
    #     """
    #     try:
    #         self.nodriver_logger.info("Scrolling down the page to load all content...")
    #         # Get total page height
    #         scroll_height = page.evaluate("() => document.body.scrollHeight")

    #         # Scroll in steps
    #         step_size = 500  # pixels per step
    #         pause = 0.3  # seconds to wait between steps

    #         for position in range(0, scroll_height, step_size):
    #             page.evaluate(f"window.scrollTo(0, {position})")
    #             time.sleep(pause)  # Let content load
    #     except Exception as e:
    #         self.nodriver_logger.error(f"Error scrolling down the page: {e}")
    #         return
    
    # def request(self, url: str, method: str, headers: dict = {}, data: dict = {}) -> str:
    #     raise NotImplementedError()