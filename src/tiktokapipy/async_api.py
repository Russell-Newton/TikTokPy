"""
Asynchronous API for data scraping
"""
import traceback
from abc import ABC, abstractmethod
from typing import Generic, List, Tuple, Type

import playwright.async_api
from playwright.async_api import (
    APIRequestContext,
    Page,
    Request,
    Route,
    TimeoutError,
    async_playwright,
)
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError
from tiktokapipy.api import (
    LightUserGetter,
    TikTokAPI,
    _DataModelT,
    _LightIterInT,
    _LightIterOutT,
)
from tiktokapipy.models.challenge import Challenge, LightChallenge, challenge_link
from tiktokapipy.models.raw_data import APIResponse
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import LightVideo, Video, video_link


class AsyncLightIter(Generic[_LightIterInT, _LightIterOutT], ABC):
    """
    Utility class to lazy-load data models retrieved under a :class:`.Challenge`, :class:`.Video`, or :class:`.User`
    so they aren't all loaded at once.
    :autodoc-skip:
    """

    def __init__(self, light_models: List[_LightIterInT], api: "AsyncTikTokAPI"):
        self._light_models = light_models
        self._api = api

    @abstractmethod
    async def fetch(self) -> _LightIterOutT:
        raise NotImplementedError

    def __aiter__(self):
        self.next_up = 0
        return self

    async def __anext__(self):
        if self.next_up == len(self._light_models):
            raise StopAsyncIteration
        out = await self.fetch()
        self.next_up += 1
        return out


class AsyncLightVideoIter(AsyncLightIter[LightVideo, Video]):
    """
    Utility class to lazy-load videos retrieved under a :class:`.Challenge` or :class:`.User` so they aren't all
    loaded at once.
    :autodoc-skip:
    """

    async def fetch(self) -> Video:
        return await self._api.video(video_link(self._light_models[self.next_up].id))


class AsyncLightChallengeIter(AsyncLightIter[LightChallenge, Challenge]):
    """
    Utility class to lazy-load challenges retrieved under a :class:`.Video` loaded at once.
    :autodoc-skip:
    """

    async def fetch(self) -> Challenge:
        return await self._api.challenge(self._light_models[self.next_up].title)


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
    def _light_challenge_iter_type(self):
        return AsyncLightChallengeIter

    @property
    def _light_user_getter_type(self):
        return AsyncLightUserGetter

    async def _scrape_data(
        self, link: str, data_model: Type[_DataModelT]
    ) -> Tuple[_DataModelT, List[APIResponse]]:
        api_extras: List[APIResponse] = []
        extras_json: List[dict] = []

        async def capture_api_extras(route: Route, request: Request):
            request_context: APIRequestContext = self.context.request
            try:
                response: playwright.async_api.APIResponse = await request_context.get(
                    request.url,
                    headers=request.headers,
                )
            except Exception:
                await route.abort()
                return
            body = await response.body()
            if len(body) > 2:
                _data = await response.json()
                extras_json.append(_data)
                api_response = APIResponse.parse_obj(_data)
                api_extras.append(api_response)
            await route.fulfill(
                status=response.status,
                headers=response.headers,
                body=body,
                response=response,
            )

        for _ in range(self.navigation_retries + 1):
            self.context.clear_cookies()
            page: Page = await self._context.new_page()
            await page.route("**/api/challenge/item_list/*", capture_api_extras)
            await page.route("**/api/comment/list/*", capture_api_extras)
            await page.route("**/api/post/item_list/*", capture_api_extras)
            try:
                await page.goto(link)
                await page.wait_for_selector("#SIGI_STATE", state="attached")

                if self.scroll_down_time > 0:
                    await self._scroll_page_down(page)

                content = await page.content()
                await page.close()

                data = self._extract_and_dump_data(content, extras_json, data_model)
            except (TimeoutError, ValidationError, IndexError) as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                await page.close()
                continue
            break
        else:
            raise TikTokAPIError(
                f"Data scraping unable to complete in {self.navigation_timeout / 1000}s "
                f"(retries: {self.navigation_retries})"
            )

        return data, api_extras

    async def challenge(self, challenge_name: str, video_limit: int = 0) -> Challenge:
        link = challenge_link(challenge_name)
        response, api_extras = await self._scrape_data(
            link, self._challenge_response_type
        )
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    async def user(self, user: str, video_limit: int = 0) -> User:
        link = user_link(user)
        response, api_extras = await self._scrape_data(link, self._user_response_type)
        return self._extract_user_from_response(response, api_extras, video_limit)

    async def video(self, link: str) -> Video:
        response, api_extras = await self._scrape_data(link, self._video_response_type)
        return self._extract_video_from_response(response, api_extras)

    async def _scroll_page_down(self, page: Page):
        await page.evaluate(
            """
            var intervalID = setInterval(function () {
                var scrollingElement = (document.scrollingElement || document.body);
                scrollingElement.scrollTop = scrollingElement.scrollHeight;
            }, 200);

            """
        )
        await page.wait_for_timeout(self.scroll_down_time * 1000)
        await page.evaluate("clearInterval(intervalID)")


__all__ = ["AsyncTikTokAPI"]
