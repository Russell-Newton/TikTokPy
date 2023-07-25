"""
Asynchronous API for data scraping
"""

from __future__ import annotations

import traceback
import warnings
from typing import Type, TypeVar, Union

from playwright.async_api import Page, Route, TimeoutError, async_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError, TikTokAPIWarning
from tiktokapipy.api import TikTokAPI
from tiktokapipy.models.challenge import Challenge
from tiktokapipy.models.raw_data import (
    ChallengePage,
    PrimaryResponseType,
    SentToLoginResponse,
    UserResponse,
    VideoPage,
)
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import Video, is_mobile_share_link
from tiktokapipy.util.queries import get_challenge_detail_async, get_video_detail_async

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

            async def ignore_scripts(route: Route):
                if route.request.resource_type == "script":
                    return await route.abort()
                return await route.continue_()

            await page.route("**/*", ignore_scripts)
            try:
                await page.goto(link, wait_until=None)
                await page.wait_for_selector("#SIGI_STATE", state="attached")
                content = await page.content()

                data = content.split(
                    '<script id="SIGI_STATE" type="application/json">'
                )[1].split("</script>")[0]

                if "LoginContextModule" in data:
                    warnings.warn(
                        "Redirected to a login page. Trying again...",
                        category=TikTokAPIWarning,
                        stacklevel=2,
                    )
                    sent_to_login = SentToLoginResponse.model_validate_json(data)
                    await page.goto(
                        sent_to_login.login_context_module.redirect_url, wait_until=None
                    )
                    await page.wait_for_selector("#SIGI_STATE", state="attached")
                    content = await page.content()
                    data = content.split(
                        '<script id="SIGI_STATE" type="application/json">'
                    )[1].split("</script>")[0]

                await page.close()

                extracted = self._extract_and_dump_data(data, data_model)
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

        return extracted

    async def challenge(
        self, challenge_name: str, *, video_limit: int = -1
    ) -> Challenge:
        response = ChallengePage.model_validate(
            await get_challenge_detail_async(challenge_name, self.context)
        )
        challenge = self._extract_challenge_from_response(response)
        challenge.videos.limit(video_limit)
        return challenge

    async def user(self, user: str, *, video_limit: int = -1) -> User:
        link = user_link(user)
        response = await self._scrape_data(
            link,
            UserResponse,
        )
        user = self._extract_user_from_response(response)
        user.videos.limit(video_limit)
        return user

    async def video(
        self,
        link_or_id: Union[int, str],
    ) -> Video:
        if isinstance(link_or_id, str):
            if is_mobile_share_link(link_or_id):
                await self.context.clear_cookies()
                page: Page = await self.context.new_page()
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

                async def ignore_scripts(route: Route):
                    if route.request.resource_type == "script":
                        return await route.abort()
                    return await route.continue_()

                await page.route("**/*", ignore_scripts)
                await page.goto(link_or_id, wait_until=None)
                await page.wait_for_selector("#SIGI_STATE", state="attached")

                link_or_id = page.url

                await page.close()
            video_id = link_or_id.split("/")[-1].split("?")[0]
        else:
            video_id = link_or_id

        response = VideoPage.model_validate(
            await get_video_detail_async(video_id, self.context)
        )
        return self._extract_video_from_response(response)


__all__ = ["AsyncTikTokAPI"]
