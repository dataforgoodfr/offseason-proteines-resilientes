from contextlib import AsyncExitStack

from scrapy_playwright.handler import PERSISTENT_CONTEXT_PATH_KEY, Config


class InvisibleBrowserProvider:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.stack = AsyncExitStack()

    async def start(self) -> None:
        pass

    async def launch_browser(self):
        from invisible_playwright.async_api import InvisiblePlaywright

        # e.g. seed / proxy / timezone / pin via PLAYWRIGHT_LAUNCH_OPTIONS
        return await self.stack.enter_async_context(
            InvisiblePlaywright(**self.config.launch_options)
        )

    async def launch_persistent_context(self, context_kwargs: dict):
        from invisible_playwright.async_api import InvisiblePlaywright

        # invisible_playwright names the profile path ``profile_dir``
        return await self.stack.enter_async_context(
            InvisiblePlaywright(
                profile_dir=context_kwargs[PERSISTENT_CONTEXT_PATH_KEY],
                **self.config.launch_options,
            )
        )

    async def close(self) -> None:
        await self.stack.aclose()
