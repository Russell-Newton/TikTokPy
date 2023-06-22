"""
Asynchronous API for data scraping
"""

from __future__ import annotations

import traceback
import warnings
from typing import Type, TypeVar

from playwright.async_api import Page, TimeoutError, async_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError, TikTokAPIWarning
from tiktokapipy.api import TikTokAPI
from tiktokapipy.models.challenge import Challenge
from tiktokapipy.models.raw_data import ChallengePage, PrimaryResponseType
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import Video
from tiktokapipy.util.queries import get_challenge_detail_async

_DataModelT = TypeVar("_DataModelT", bound=PrimaryResponseType, covariant=True)
"""
Generic used for data scraping.
"""


class AsyncTikTokAPI(TikTokAPI):
    """Asynchronous API used to scrape data from TikTok"""

    def __enter__(self):
        raise TikTokAPIError("Must use async context manager with AsyncTikTokAPI")

    async def __aenter__(self) -> AsyncTikTokAPI:
        self._playwright = await async_playwright().start()
        self._browser = await self.playwright.chromium.launch(
            headless=self.headless, **self.kwargs
        )

        context_kwargs = self.context_kwargs

        if self.emulate_mobile:
            context_kwargs.update(self.playwright.devices["iPhone 12"])
        else:
            context_kwargs.update(self.playwright.devices["Desktop Edge"])

        self._context = await self.browser.new_context(**context_kwargs)
        self.context.set_default_navigation_timeout(self.navigation_timeout)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def _scrape_data(
        self,
        link: str,
        data_model: Type[_DataModelT],
    ) -> _DataModelT:
        for _ in range(self.navigation_retries + 1):
            await self.context.clear_cookies()
            page: Page = await self._context.new_page()
            await page.add_init_script(
                """
if (navigator.webdriver === false) {
    // Post Chrome 89.0.4339.0 and already good
} else if (navigator.webdriver === undefined) {
    // Pre Chrome 89.0.4339.0 and already good
} else {
    // Pre Chrome 88.0.4291.0 and needs patching
    delete Object.getPrototypeOf(navigator).webdriver
}
            """
            )
            try:
                await page.goto(link, wait_until=None)
                await page.wait_for_selector("#SIGI_STATE", state="attached")

                content = await page.content()
                await page.close()

                data = self._extract_and_dump_data(content, data_model)
            except (ValidationError, IndexError) as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                await page.close()
                continue
            except TimeoutError:
                warnings.warn(
                    "Reached navigation timeout. Retrying...",
                    category=TikTokAPIWarning,
                    stacklevel=2,
                )
                await page.close()
                continue
            break
        else:
            raise TikTokAPIError(
                f"Data scraping unable to complete in {self.navigation_timeout / 1000}s "
                f"(retries: {self.navigation_retries})"
            )

        return data

    async def challenge(
        self,
        challenge_name: str,
    ) -> Challenge:
        response = ChallengePage.model_validate(
            await get_challenge_detail_async(challenge_name, self.context)
        )
        return self._extract_challenge_from_response(response)

    async def user(
        self,
        user: str,
    ) -> User:
        link = user_link(user)
        response = await self._scrape_data(
            link,
            self._user_response_type,
        )
        return self._extract_user_from_response(response)

    async def video(
        self,
        link: str,
    ) -> Video:
        response = await self._scrape_data(
            link,
            self._video_response_type,
        )
        return self._extract_video_from_response(response)


__all__ = ["AsyncTikTokAPI"]
