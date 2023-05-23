"""
Asynchronous API for data scraping
"""

from __future__ import annotations

import json
import traceback
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Generic, List, Tuple, Type

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

import playwright.async_api
from playwright.async_api import Page, Route, TimeoutError, async_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError, TikTokAPIWarning
from tiktokapipy.api import (
    LightUserGetter,
    TikTokAPI,
    _DataModelT,
    _LightIterInT,
    _LightIterOutT,
)
from tiktokapipy.models import AsyncDeferredIterator
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

    def __init__(self, light_models: List[_LightIterInT], api: AsyncTikTokAPI):
        self.light_models: List[_LightIterInT] = light_models
        self._api = api

    @abstractmethod
    async def fetch(self, idx: int) -> _LightIterOutT:
        ...

    def sorted_by(
        self, key: Callable[[_LightIterInT], SupportsLessThan], reverse: bool = False
    ) -> AsyncLightIter[_LightIterInT, _LightIterOutT]:
        return self.__class__(
            sorted(self.light_models, key=key, reverse=reverse), self._api
        )

    def __aiter__(self) -> AsyncLightIter[_LightIterInT, _LightIterOutT]:
        self._next_up = 0
        return self

    async def __anext__(self) -> _LightIterOutT:
        if self._next_up == len(self.light_models):
            raise StopAsyncIteration
        out = await self.fetch(self._next_up)
        self._next_up += 1
        return out


class AsyncLightVideoIter(AsyncLightIter[LightVideo, Video]):
    """
    Utility class to lazy-load videos retrieved under a :class:`.Challenge` or :class:`.User` so they aren't all
    loaded at once.
    :autodoc-skip:
    """

    async def fetch(self, idx: int) -> Video:
        return await self._api.video(video_link(self.light_models[idx].id))


class AsyncLightChallengeIter(AsyncLightIter[LightChallenge, Challenge]):
    """
    Utility class to lazy-load challenges retrieved under a :class:`.Video` loaded at once.
    :autodoc-skip:
    """

    async def fetch(self, idx: int) -> Challenge:
        return await self._api.challenge(self.light_models[idx].title)


class AsyncLightUserGetter(LightUserGetter):
    """:autodoc-skip:"""

    async def __call__(self) -> User:
        return await self._api.user(self.light_user.unique_id)


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

    @property
    def _light_videos_iter_type(self) -> Type[AsyncDeferredIterator[LightVideo, Video]]:
        return AsyncLightVideoIter

    @property
    def _light_challenge_iter_type(
        self,
    ) -> Type[AsyncDeferredIterator[LightChallenge, Challenge]]:
        return AsyncLightChallengeIter

    @property
    def _light_user_getter_type(self):
        return AsyncLightUserGetter

    async def _scrape_data(
        self,
        link: str,
        data_model: Type[_DataModelT],
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> Tuple[_DataModelT, List[APIResponse]]:

        if scroll_down_time is None:
            scroll_down_time = self.default_scroll_down_time

        if scroll_down_delay is None:
            scroll_down_delay = self.default_scroll_down_delay

        if scroll_down_iter_delay is None:
            scroll_down_iter_delay = self.default_scroll_down_iter_delay

        api_extras: List[APIResponse] = []
        extras_json: List[dict] = []

        async def capture_api_extras(route: Route):
            try:
                await route.continue_()
                response = await route.request.response()
            except playwright.async_api.Error:
                return

            if not response:
                return

            try:
                _data = await response.json()
            except json.JSONDecodeError:
                return

            extras_json.append(_data)
            api_response = APIResponse.parse_obj(_data)
            api_extras.append(api_response)

        for _ in range(self.navigation_retries + 1):
            await self.context.clear_cookies()
            page: Page = await self._context.new_page()
            await page.route("**/api/challenge/item_list/**", capture_api_extras)
            await page.route("**/api/comment/list/**", capture_api_extras)
            await page.route("**/api/post/item_list/**", capture_api_extras)
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

                if self.default_scroll_down_time > 0:
                    await self._scroll_page_down(
                        page,
                        scroll_down_time,
                        scroll_down_delay,
                        scroll_down_iter_delay,
                    )

                content = await page.content()
                await page.close()

                data = self._extract_and_dump_data(content, extras_json, data_model)
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

        return data, api_extras

    async def challenge(
        self,
        challenge_name: str,
        video_limit: int = 0,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> Challenge:
        link = challenge_link(challenge_name)
        response, api_extras = await self._scrape_data(
            link,
            self._challenge_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    async def user(
        self,
        user: str,
        video_limit: int = 0,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> User:
        link = user_link(user)
        response, api_extras = await self._scrape_data(
            link,
            self._user_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_user_from_response(response, api_extras, video_limit)

    async def video(
        self,
        link: str,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> Video:
        response, api_extras = await self._scrape_data(
            link,
            self._video_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_video_from_response(response, api_extras)

    async def _scroll_page_down(
        self,
        page: Page,
        scroll_down_time: float,
        scroll_down_delay: float,
        scroll_down_iter_delay: float,
    ):
        await page.wait_for_timeout(scroll_down_delay * 1000)
        await page.evaluate(
            """
var down = true;
var intervalID = setInterval(function () {
    var scrollingElement = (document.scrollingElement || document.body);
    if (down) {
        scrollingElement.scrollTop = scrollingElement.scrollHeight;
    } else {
        scrollingElement.scrollTop = scrollingElement.scrollTop - 100;
    }
    down = !down;
},
            """
            + str(scroll_down_iter_delay * 1000)
            + ");"
        )
        await page.wait_for_timeout(scroll_down_time * 1000)
        await page.evaluate("clearInterval(intervalID)")


__all__ = ["AsyncTikTokAPI"]
