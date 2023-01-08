"""
Asynchronous API for data scraping
"""

from __future__ import annotations

import json
import traceback
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, Tuple, Type

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

import playwright.async_api
from playwright.async_api import Page, Route, TimeoutError, async_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError
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
from tiktokapipy.models.user import LightUser, User, user_link
from tiktokapipy.models.video import LightVideo, Video, video_link


class AsyncLightIter(Generic[_LightIterInT, _LightIterOutT], ABC):
    """
    Utility class to lazy-load data models retrieved under a :class:`.Challenge`, :class:`.Video`, or :class:`.User`
    so they aren't all loaded at once.
    :autodoc-skip:
    """

    def __init__(self, light_models: List[_LightIterInT], api: AsyncTikTokAPI):
        self._light_models = light_models
        self._api = api

    @abstractmethod
    async def fetch(self, idx: int) -> _LightIterOutT:
        ...

    def sorted_by(
        self, key: Callable[[_LightIterInT], SupportsLessThan], reverse: bool = False
    ) -> AsyncLightIter[_LightIterInT, _LightIterOutT]:
        return self.__class__(
            sorted(self._light_models, key=key, reverse=reverse), self._api
        )

    def __aiter__(self) -> AsyncLightIter[_LightIterInT, _LightIterOutT]:
        self._next_up = 0
        return self

    async def __anext__(self) -> _LightIterOutT:
        if self._next_up == len(self._light_models):
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
        return await self._api.video(video_link(self._light_models[idx].id))


class AsyncLightUserIter(AsyncLightIter[LightUser, User]):
    """
    Utility class to lazy-load users retrieved as a class:`.User`'s follower/following list so they aren't all
    loaded at once.
    :autodoc-skip:
    """

    async def fetch(self, idx: int) -> User:
        return await self._api.user(self._light_models[idx].unique_id)


class AsyncLightChallengeIter(AsyncLightIter[LightChallenge, Challenge]):
    """
    Utility class to lazy-load challenges retrieved under a :class:`.Video` loaded at once.
    :autodoc-skip:
    """

    async def fetch(self, idx: int) -> Challenge:
        return await self._api.challenge(self._light_models[idx].title)


class AsyncLightUserGetter(LightUserGetter):
    """:autodoc-skip:"""

    async def __call__(self) -> User:
        return await self._api.user(self._user.unique_id)


class AsyncTikTokAPI(TikTokAPI):
    """Asynchronous API used to scrape data from TikTok"""

    def __enter__(self):
        raise TikTokAPIError("Must use async context manager with AsyncTikTokAPI")

    async def __aenter__(self) -> AsyncTikTokAPI:
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

    def _light_videos_iter(
        self, models: List[LightVideo]
    ) -> AsyncDeferredIterator[LightVideo, Video]:
        return AsyncLightVideoIter(models, self)

    def _light_user_list_iter(
        self, models: List[LightUser]
    ) -> AsyncDeferredIterator[LightUser, User]:
        return AsyncLightUserIter(models, self)

    def _light_challenge_iter(
        self, models: List[LightChallenge]
    ) -> AsyncDeferredIterator[LightChallenge, Challenge]:
        return AsyncLightChallengeIter(models, self)

    def _light_user_getter(self, user: str):
        return AsyncLightUserGetter(user, self)

    async def _scrape_data(
        self, link: str, data_model: Type[_DataModelT]
    ) -> Tuple[_DataModelT, List[APIResponse]]:
        api_extras: List[APIResponse] = []
        extras_json: List[dict] = []

        async def capture_api_extras(route: Route):
            try:
                response = await route.fetch()
            except playwright.async_api.Error:
                return

            try:
                _data = await response.json()
            except json.JSONDecodeError:
                await route.fulfill(response=response)
                return

            extras_json.append(_data)
            api_response = APIResponse.parse_obj(_data)
            api_extras.append(api_response)
            await route.fulfill(
                response=response,
                json=_data,
            )

        for _ in range(self.navigation_retries + 1):
            await self.context.clear_cookies()
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
        user = self._extract_user_from_response(response, api_extras, video_limit)

        user.following = await self._grab_user_list(21, user.sec_uid)
        user.followers = await self._grab_user_list(67, user.sec_uid)

        return user

    async def video(self, link: str) -> Video:
        response, api_extras = await self._scrape_data(link, self._video_response_type)
        return self._extract_video_from_response(response, api_extras)

    async def _grab_user_list(
        self, scene: int, sec_uid: str
    ) -> Optional[AsyncDeferredIterator[LightUser, User]]:
        min_cursor = 0
        out_list = []
        try:
            while min_cursor != -1:
                list_request = await self.context.request.fetch(
                    f"https://us.tiktok.com/api/user/list/"
                    f"?minCursor={min_cursor}&scene={scene}&count=200&secUid={sec_uid}"
                )
                print(list_request)
                response = APIResponse.parse_obj(list_request.json())
                if response.status_code == 10222:
                    raise TikTokAPIError("The requested user list is set to private.")

                user_list = response.user_list
                if user_list:
                    out_list.extend([item.user for item in user_list])

                min_cursor = response.min_cursor

            return self._light_user_list_iter(out_list)
        except (playwright.async_api.Error, json.JSONDecodeError, TikTokAPIError) as e:
            warnings.warn(f"Was unable to grab user list from scene {scene}:\n{e}")
            return None

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
