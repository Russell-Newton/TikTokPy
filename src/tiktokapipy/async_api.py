"""
Asynchronous API for data scraping
"""

import asyncio
import json
from typing import List, Tuple, Type

import requests
from playwright.async_api import Page, Request, Route, TimeoutError, async_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError
from tiktokapipy.api import DataModelT, LightUserGetter, LightVideosIter, TikTokAPI
from tiktokapipy.models.challenge import Challenge, challenge_link
from tiktokapipy.models.raw_data import APIResponse
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import Video, video_link


class AsyncLightVideoIter(LightVideosIter):
    """:autodoc-skip:"""

    async def fetch_video(self) -> Video:
        video = await self._api.video(video_link(self._videos[self.next_up].id))
        self.next_up += 1
        return video

    def __aiter__(self) -> "LightVideosIter":
        self.next_up = 0
        return self

    async def __anext__(self) -> Video:
        if self.next_up == len(self._videos):
            raise StopAsyncIteration
        return await self.fetch_video()


class AsyncLightUserGetter(LightUserGetter):
    """:autodoc-skip:"""

    async def __call__(self) -> User:
        return await self._api.user(self._user.unique_id)


class AsyncTikTokAPI(TikTokAPI):
    """Asynchronous API used to scrape data from TikTok"""

    def __enter__(self):
        raise TikTokAPIError("Must use async context manager with AsyncTikTokAPI")

    async def __aenter__(self) -> "AsyncTikTokAPI":
        self._playwright = await async_playwright().start()

        self._browser = await self.playwright.chromium.launch(headless=self.headless)

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

    @property
    def _light_videos_iter_type(self):
        return AsyncLightVideoIter

    @property
    def _light_user_getter_type(self):
        return AsyncLightUserGetter

    async def _scrape_data(
        self, link: str, data_model: Type[DataModelT]
    ) -> Tuple[DataModelT, List[APIResponse]]:
        api_extras = []
        extras_json = []

        async def capture_api_extras(route: Route, request: Request):
            r = requests.get(
                request.url,
                headers=request.headers,
                cookies={
                    cookie["name"]: cookie["value"]
                    for cookie in await self._context.cookies()
                },
            )
            if len(r.content) > 2:
                extras_json.append(json.loads(r.content.decode("utf-8")))
                api_response = APIResponse.parse_raw(r.content)
                api_extras.append(api_response)
            await route.continue_()

        page: Page = await self._context.new_page()
        await page.route("**/api/challenge/item_list/*", capture_api_extras)
        await page.route("**/api/comment/list/*", capture_api_extras)
        await page.route("**/api/post/item_list/*", capture_api_extras)

        for _ in range(self.navigation_retries + 1):
            try:
                await page.goto(link, wait_until=self.wait_until)

                if self.scroll_down_time > 0:
                    await self._scroll_page_down(page, self.scroll_down_time)

                content = await page.content()

                data = self._extract_and_dump_data(content, extras_json, data_model)
            except (TimeoutError, ValidationError, IndexError):
                continue
            break
        else:
            raise TikTokAPIError(
                f"Data scraping unable to complete in {self.navigation_timeout / 1000}s "
                f"(retries: {self.navigation_retries})"
            )

        await page.close()

        return data, api_extras

    async def challenge(self, challenge_name: str, video_limit: int = 25) -> Challenge:
        link = challenge_link(challenge_name)
        response, api_extras = await self._scrape_data(
            link, self._challenge_response_type
        )
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    async def user(self, user: str, video_limit: int = 25) -> User:
        link = user_link(user)
        response, api_extras = await self._scrape_data(link, self._user_response_type)
        return self._extract_user_from_response(response, api_extras, video_limit)

    async def video(self, link: str) -> Video:
        response, api_extras = await self._scrape_data(link, self._video_response_type)
        return self._extract_video_from_response(response, api_extras)

    async def _scroll_page_down(self, page: Page, scroll_down_time: float):
        await page.evaluate(
            """
            var intervalID = setInterval(function () {
                var scrollingElement = (document.scrollingElement || document.body);
                scrollingElement.scrollTop = scrollingElement.scrollHeight;
            }, 200);

            """
        )
        # prev_height = None
        # done = False
        # its = 0
        # while not done:
        #     curr_height = await page.evaluate('(window.innerHeight + window.scrollY)')
        #     if not prev_height:
        #         prev_height = curr_height
        #         await asyncio.sleep(2)
        #     elif prev_height == curr_height:
        #         done = True
        #     else:
        #         prev_height = curr_height
        #         await asyncio.sleep(2)
        #
        #     its += 1
        #     if its >= time:
        #         done = True
        await asyncio.sleep(scroll_down_time)

        await page.evaluate("clearInterval(intervalID)")


__all__ = ["AsyncTikTokAPI"]
