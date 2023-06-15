import abc
import time
from typing import List, Literal, Union

from playwright.async_api import BrowserContext as AsyncBrowserContext
from playwright.sync_api import BrowserContext as SyncBrowserContext
from tiktokapipy import TikTokAPIError
from tiktokapipy.util.queries import (
    get_challenge_detail_async,
    get_challenge_detail_sync,
    make_request_async,
    make_request_sync,
)


class DeferredIterator(abc.ABC):
    def __init__(self, api):
        self._api = api
        self._collected_values = []
        self.head = 0
        self.cursor = 0
        self.has_more = True

    @abc.abstractmethod
    def fetch_sync(self):
        pass

    @abc.abstractmethod
    async def fetch_async(self):
        pass

    def __iter__(self):
        if isinstance(self._api.context, AsyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use AsyncTikTokAPI in a synchronous context. Use `async for` instead."
            )
        self.head = 0
        return self

    def __next__(self):
        if isinstance(self._api.context, AsyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use AsyncTikTokAPI in a synchronous context. Use `async for` instead."
            )
        if self.head == len(self._collected_values):
            if not self.has_more:
                raise StopIteration
            self.fetch_sync()
        out = self._collected_values[self.head]
        self.head += 1
        return out

    def __aiter__(self):
        if isinstance(self._api.context, SyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use TikTokAPI in an asynchronous context. Use `for` instead."
            )
        self.head = 0
        return self

    async def __anext__(self):
        if isinstance(self._api.context, SyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use TikTokAPI in an asynchronous context. Use `for` instead."
            )
        if self.head == len(self._collected_values):
            if not self.has_more:
                raise StopAsyncIteration
            await self.fetch_async()
        out = self._collected_values[self.head]
        self.head += 1
        return out


class DeferredCommentIterator(DeferredIterator):
    def __init__(self, api, video_id: int):
        super().__init__(api)
        self._video_id = video_id

    def fetch_sync(self):
        from tiktokapipy.models.raw_data import APIResponse

        raw = make_request_sync(
            "comment/list/", self.cursor, self._video_id, self._api.context
        )
        converted = APIResponse.model_validate(raw)
        for comment in converted.comments:
            comment._api = self._api
        self.has_more = converted.has_more
        self._collected_values += converted.comments
        self.cursor = converted.cursor

    async def fetch_async(self):
        from tiktokapipy.models.raw_data import APIResponse

        raw = await make_request_async(
            "comment/list/", self.cursor, self._video_id, self._api.context
        )
        converted = APIResponse.model_validate(raw)
        for comment in converted.comments:
            comment._api = self._api
        self.has_more = converted.has_more
        self._collected_values += converted.comments
        self.cursor = converted.cursor


class DeferredItemListIterator(DeferredIterator):
    def __init__(
        self,
        api,
        from_type: Literal["post", "challenge"],
        target_id: Union[int, str],
        **extra_params,
    ):
        super().__init__(api)
        self.from_type = from_type
        self._target_id = target_id
        self._extra_params = extra_params

        if self.from_type == "post":
            self.cursor = int(time.time()) * 1000

    def fetch_sync(self):
        from tiktokapipy.models.raw_data import APIResponse

        # noinspection PyTypeChecker
        raw = make_request_sync(
            f"{self.from_type}/item_list/",
            self.cursor,
            self._target_id,
            self._api.context,
            **self._extra_params,
        )
        converted = APIResponse.model_validate(raw)
        for item in converted.item_list:
            item._api = self._api
        self.has_more = converted.has_more
        self._collected_values += converted.item_list
        self.cursor = converted.cursor

    async def fetch_async(self):
        from tiktokapipy.models.raw_data import APIResponse

        # noinspection PyTypeChecker
        raw = await make_request_async(
            f"{self.from_type}/item_list/",
            self.cursor,
            self._target_id,
            self._api.context,
            **self._extra_params,
        )
        converted = APIResponse.model_validate(raw)
        for item in converted.item_list:
            item._api = self._api
        self.has_more = converted.has_more
        self._collected_values += converted.item_list
        self.cursor = converted.cursor


class DeferredChallengeIterator:
    def __init__(self, api, challenge_names: List[str]):
        from tiktokapipy.models.challenge import Challenge

        self._api = api
        self._collected_values: List[Challenge] = []
        self._challenge_names = challenge_names
        self.head = 0

    def fetch_sync(self):
        from tiktokapipy.models.raw_data import ChallengePage

        converted = ChallengePage.model_validate(
            get_challenge_detail_sync(
                self._challenge_names[self.head], self._api.context
            )
        )
        challenge = converted.challenge_info.challenge
        challenge._api = self._api
        self._collected_values.append(challenge)

    async def fetch_async(self):
        from tiktokapipy.models.raw_data import ChallengePage

        converted = ChallengePage.model_validate(
            await get_challenge_detail_async(
                self._challenge_names[self.head], self._api.context
            )
        )
        challenge = converted.challenge_info.challenge
        challenge._api = self._api
        self._collected_values.append(challenge)

    def __iter__(self):
        if isinstance(self._api.context, AsyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use AsyncTikTokAPI in a synchronous context. Use `async for` instead."
            )
        self.head = 0
        return self

    def __next__(self):
        if isinstance(self._api.context, AsyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use AsyncTikTokAPI in a synchronous context. Use `async for` instead."
            )
        if self.head == len(self._collected_values):
            if self.head == len(self._challenge_names):
                raise StopIteration
            self.fetch_sync()
        out = self._collected_values[self.head]
        self.head += 1
        return out

    def __aiter__(self):
        if isinstance(self._api.context, SyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use TikTokAPI in an asynchronous context. Use `for` instead."
            )
        self.head = 0
        return self

    async def __anext__(self):
        if isinstance(self._api.context, SyncBrowserContext):
            raise TikTokAPIError(
                "Attempting to use TikTokAPI in an asynchronous context. Use `for` instead."
            )
        if self.head == len(self._collected_values):
            if self.head == len(self._challenge_names):
                raise StopIteration
            await self.fetch_async()
        out = self._collected_values[self.head]
        self.head += 1
        return out


class SyncDeferredUserGetter:
    def __init__(self, api, unique_id: str):
        self._api = api
        self._unique_id = unique_id
        self._user = None

    def __call__(self):
        if self._user is None:
            self._user = self._api.user(self._unique_id)
            self._user._api = self._api
        return self._user


class AsyncDeferredUserGetter:
    def __init__(self, api, unique_id: str):
        self._api = api
        self._unique_id = unique_id
        self._user = None

    async def __call__(self):
        if self._user is None:
            self._user = await self._api.user(self._unique_id)
            self._user._api = self._api
        return self._user