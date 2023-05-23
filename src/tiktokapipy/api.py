"""
Synchronous API for data scraping
"""

from __future__ import annotations

import json
import traceback
import warnings
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

import playwright.sync_api
from playwright.sync_api import Page, Route, TimeoutError, sync_playwright
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError, TikTokAPIWarning
from tiktokapipy.models import DeferredIterator, TikTokDataModel
from tiktokapipy.models.challenge import Challenge, LightChallenge, challenge_link
from tiktokapipy.models.raw_data import (
    APIResponse,
    ChallengeResponse,
    MobileChallengeResponse,
    MobileResponseMixin,
    MobileUserResponse,
    MobileVideoResponse,
    PrimaryResponseType,
    UserResponse,
    VideoResponse,
)
from tiktokapipy.models.user import LightUser, User, user_link
from tiktokapipy.models.video import LightVideo, Video, video_link

_DataModelT = TypeVar("_DataModelT", bound=PrimaryResponseType, covariant=True)
"""
Generic used for data scraping.
"""
_LightIterInT = TypeVar("_LightIterInT", bound=TikTokDataModel, covariant=True)
"""
Generic used as LightIter input type.
"""
_LightIterOutT = TypeVar("_LightIterOutT", bound=TikTokDataModel, covariant=True)
"""
Generic used as LightIter output type.
"""


class LightIter(Generic[_LightIterInT, _LightIterOutT], Iterator[_LightIterOutT], ABC):
    """
    Utility class to lazy-load data models retrieved under a :class:`.Challenge`, :class:`.Video`, or :class:`.User`
    so they aren't all loaded at once.
    :autodoc-skip:
    """

    def __init__(self, light_models: List[_LightIterInT], api: TikTokAPI):
        self.light_models: List[_LightIterInT] = light_models
        self._api = api

    @abstractmethod
    def fetch(self, idx: int) -> _LightIterOutT:
        ...

    def sorted_by(
        self, key: Callable[[_LightIterInT], SupportsLessThan], reverse: bool = False
    ) -> LightIter[_LightIterInT, _LightIterOutT]:
        return self.__class__(
            sorted(self.light_models, key=key, reverse=reverse), self._api
        )

    def __iter__(self) -> LightIter[_LightIterInT, _LightIterOutT]:
        self._next_up = 0
        return self

    def __next__(self) -> _LightIterOutT:
        if self._next_up == len(self.light_models):
            raise StopIteration
        out = self.fetch(self._next_up)
        self._next_up += 1
        return out


class LightVideoIter(LightIter[LightVideo, Video]):
    """
    Utility class to lazy-load videos retrieved under a :class:`.Challenge` or :class:`.User` so they aren't all
    loaded at once.
    :autodoc-skip:
    """

    def fetch(self, idx: int) -> Video:
        return self._api.video(video_link(self.light_models[idx].id))


class LightChallengeIter(LightIter[LightChallenge, Challenge]):
    """
    Utility class to lazy-load challenges retrieved under a :class:`.Video` loaded at once.
    :autodoc-skip:
    """

    def fetch(self, idx: int) -> Challenge:
        return self._api.challenge(self.light_models[idx].title)


class LightUserGetter:
    """
    Utility class to lazy-load a user retrieved under a :class:`.Comment` or :class:`.Video` so they aren't all loaded
    at once.
    :autodoc-skip:
    """

    def __init__(self, user: str, api: TikTokAPI):
        self.light_user = LightUser(unique_id=user)
        self._api = api

    def __call__(self) -> User:
        return self._api.user(self.light_user.unique_id)


class TikTokAPI:
    """Synchronous API used to scrape data from TikTok"""

    def __init__(
        self,
        *,
        scroll_down_time: float = 0,
        scroll_down_delay: float = 1,
        scroll_down_iter_delay: float = 0.2,
        headless: bool = None,
        data_dump_file: str = None,
        emulate_mobile: bool = False,
        navigation_timeout: float = 30,
        navigation_retries: int = 0,
        context_kwargs: dict = None,
        navigator_type: Optional[
            Literal["Firefox", "firefox", "Chromium", "chromium"]
        ] = None,
        **kwargs,
    ):
        """
        :param scroll_down_time: How much time (in seconds) should the page navigation include scrolling down. This can
            load more content from the page. This is the default time for all API calls. It can be overridden in each
            call.
        :param scroll_down_delay: How much time (in seconds) should pass before starting scrolling down. It is suggested
            that this be more than 0, as no delay can result in API deadlocks on TikTok. Like ``scroll_down_time``, this
            can be overridden in each call.
        :param scroll_down_iter_delay: How much time (in seconds) should pass between scrolls. Like
            ``scroll_down_time``, this can be overridden in each call.
        :param headless: Whether to use headless browsing.
        :param data_dump_file: If the data scraped from TikTok should also be dumped to a JSON file before parsing,
            specify the name of the dump file (exluding '.json').
        :param emulate_mobile: Whether to emulate a mobile device during sraping. Required for retrieving data
            on slideshows.
        :param navigation_timeout: How long (in milliseconds) page navigation should wait before timing out. Set to 0 to
            disable the timeout.
        :param navigation_retries: How many times to retry navigation if ``network_timeout`` is exceeded. Set to 0 to
            not retry navigation.
        :param context_kwargs: Any extra kwargs used to initialize the playwright browser context. For full details,
            see `Browser::new_context() <https://playwright.dev/python/docs/api/class-browser#browser-new-context>`_.
        :param navigator_type: **DEPRECATED as of 0.1.13**, left in for backwards-compatibility.
        :param kwargs: Any extra kwargs used to initialize the playwright browser (e.g.: proxy, etc.).
            For full details, see
            `BrowserType::launch() <https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch>`_.
        """
        self.default_scroll_down_time = scroll_down_time
        self.default_scroll_down_delay = scroll_down_delay
        self.default_scroll_down_iter_delay = scroll_down_iter_delay
        self.headless = headless
        self.data_dump_file = data_dump_file
        self.emulate_mobile = emulate_mobile
        self.context_kwargs = context_kwargs or {}
        self.navigation_timeout = navigation_timeout * 1000
        self.navigation_retries = navigation_retries
        self.kwargs = kwargs
        if navigator_type is not None:
            warnings.warn(
                "The navigator_type parameter is deprecated. Chromium is always used as of 0.1.13.",
                category=DeprecationWarning,
                stacklevel=2,
            )

    def __enter__(self) -> TikTokAPI:
        self._playwright = sync_playwright().start()
        self._browser = self.playwright.chromium.launch(
            headless=self.headless, **self.kwargs
        )

        context_kwargs = self.context_kwargs

        if self.emulate_mobile:
            context_kwargs.update(self.playwright.devices["iPhone 12"])
        else:
            context_kwargs.update(self.playwright.devices["Desktop Edge"])

        self._context = self.browser.new_context(**context_kwargs)
        self.context.set_default_navigation_timeout(self.navigation_timeout)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    @property
    def playwright(self):
        """The playwright instance used for data scraping"""
        if not hasattr(self, "_playwright"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._playwright

    @property
    def browser(self):
        """The playwright Browser instance used for data scraping"""
        if not hasattr(self, "_browser"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._browser

    @property
    def context(self):
        """The playwright Context instance used for data scraping"""
        if not hasattr(self, "_context"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._context

    @property
    def _light_videos_iter_type(self) -> Type[DeferredIterator[LightVideo, Video]]:
        return LightVideoIter

    @property
    def _light_challenge_iter_type(
        self,
    ) -> Type[DeferredIterator[LightChallenge, Challenge]]:
        return LightChallengeIter

    @property
    def _light_user_getter_type(self):
        return LightUserGetter

    @property
    def _challenge_response_type(self):
        if self.emulate_mobile:
            return MobileChallengeResponse
        return ChallengeResponse

    @property
    def _user_response_type(self):
        if self.emulate_mobile:
            return MobileUserResponse
        return UserResponse

    @property
    def _video_response_type(self):
        if self.emulate_mobile:
            return MobileVideoResponse
        return VideoResponse

    def challenge(
        self,
        challenge_name: str,
        video_limit: int = 0,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> Challenge:
        """
        Retrieve data on a :class:`.Challenge` (hashtag) from TikTok. Only up to the ``video_limit`` most recent videos
        will be retrievable by the scraper.

        :param challenge_name: The name of the challenge. e.g.: ``"fyp"``
        :param video_limit: The max number of recent videos to retrieve. Set to 0 for no limit
        :param scroll_down_time: Optional override for value used in API constructor.
        :param scroll_down_delay: Optional override for value used in API constructor.
        :param scroll_down_iter_delay: Optional override for value used in API constructor.
        :return: A :class:`.Challenge` object containing the scraped data
        :rtype: :class:`.Challenge`
        """
        link = challenge_link(challenge_name)
        response, api_extras = self._scrape_data(
            link,
            self._challenge_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    def user(
        self,
        user: Union[int, str],
        video_limit: int = 0,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> User:
        """
        Retrieve data on a :class:`.User` from TikTok. Only up to the ``video_limit`` most recent videos will be
        retrievable by the scraper.

        :param user: The unique user or id of the user. e.g.: for @tiktok, use ``"tiktok"``
        :param video_limit: The max number of recent videos to retrieve. Set to 0 for no limit
        :param scroll_down_time: Optional override for value used in API constructor.
        :param scroll_down_delay: Optional override for value used in API constructor.
        :param scroll_down_iter_delay: Optional override for value used in API constructor.
        :return: A :class:`.User` object containing the scraped data
        :rtype: :class:`.User`
        """
        link = user_link(user)
        response, api_extras = self._scrape_data(
            link,
            self._user_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_user_from_response(response, api_extras, video_limit)

    def video(
        self,
        link: str,
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> Video:
        """
        Retrieve data on a :class:`.Video` from TikTok. If the video is a slideshow, :attr:`.emulate_mobile` must be
        set to ``True`` at API initialization or this method will raise a :exc:`TikTokAPIError`.

        :param link: The link to the video. Can be found from a unique video id with :func:`.video_link`.
        :param scroll_down_time: Optional override for value used in API constructor.
        :param scroll_down_delay: Optional override for value used in API constructor.
        :param scroll_down_iter_delay: Optional override for value used in API constructor.
        :return: A :class:`.Video` object containing the scraped data
        :rtype: :class:`.Video`
        """
        response, api_extras = self._scrape_data(
            link,
            self._video_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_video_from_response(response, api_extras)

    def _scrape_data(
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

        def capture_api_extras(route: Route):
            try:
                route.continue_()
                response = route.request.response()
            except playwright.sync_api.Error:
                return

            if not response:
                return

            try:
                _data = response.json()
            except json.JSONDecodeError:
                return

            extras_json.append(_data)
            api_response = APIResponse.parse_obj(_data)
            api_extras.append(api_response)

        for _ in range(self.navigation_retries + 1):
            self.context.clear_cookies()
            page: Page = self.context.new_page()
            page.route("**/api/challenge/item_list/**", capture_api_extras)
            page.route("**/api/comment/list/**", capture_api_extras)
            page.route("**/api/post/item_list/**", capture_api_extras)
            page.add_init_script(
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
                page.goto(link, wait_until=None)
                page.wait_for_selector("#SIGI_STATE", state="attached")

                if scroll_down_time > 0:
                    self._scroll_page_down(
                        page,
                        scroll_down_time,
                        scroll_down_delay,
                        scroll_down_iter_delay,
                    )

                content = page.content()
                page.close()

                data = self._extract_and_dump_data(content, extras_json, data_model)
            except (ValidationError, IndexError) as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                page.close()
                continue
            except TimeoutError:
                warnings.warn(
                    "Reached navigation timeout. Retrying...",
                    category=TikTokAPIWarning,
                    stacklevel=2,
                )
                page.close()
                continue
            break
        else:
            raise TikTokAPIError(
                f"Data scraping unable to complete in {self.navigation_timeout / 1000}s "
                f"(retries: {self.navigation_retries})"
            )

        return data, api_extras

    def _extract_and_dump_data(
        self, page_content: str, extras_json: List[dict], data_model: Type[_DataModelT]
    ):
        data = page_content.split('<script id="SIGI_STATE" type="application/json">')[
            1
        ].split("</script>")[0]

        if self.data_dump_file:
            with open(
                f"{self.data_dump_file}.{data_model.__name__}.json",
                "w+",
                encoding="utf-8",
            ) as f:
                j = json.loads(data)
                j["extras"] = extras_json
                json.dump(j, f, indent=2)

        parsed = data_model.parse_raw(data)
        if isinstance(parsed, MobileResponseMixin):
            parsed = parsed.to_desktop()
        return parsed

    def _extract_challenge_from_response(
        self,
        response: Union[ChallengeResponse, MobileChallengeResponse],
        api_extras: List[APIResponse],
        video_limit: int = 0,
    ):
        if response.challenge_page.status_code:
            raise TikTokAPIError(
                f"Error in challenge extraction: status code {response.challenge_page.status_code}"
            )
        challenge = response.challenge_page.challenge_info.challenge
        stats = response.challenge_page.challenge_info.stats
        challenge.stats = stats
        challenge.videos = self._create_video_iter(response, api_extras, video_limit)

        return challenge

    def _extract_user_from_response(
        self,
        response: Union[UserResponse, MobileUserResponse],
        api_extras: List[APIResponse],
        video_limit: int = 0,
    ):
        if response.user_page.status_code:
            raise TikTokAPIError(
                f"Error in user extraction: status code {response.user_page.status_code}"
            )
        name, user = list(response.user_module.users.items())[0]
        user.stats = response.user_module.stats[name]
        user.videos = self._create_video_iter(response, api_extras, video_limit)

        return user

    def _create_video_iter(
        self,
        response: Union[ChallengeResponse, UserResponse],
        api_extras: List[APIResponse],
        video_limit: int = 25,
    ):
        videos = list(response.item_module.values())
        if api_extras:
            for extra in api_extras:
                if extra.item_list:
                    videos += extra.item_list
        if video_limit > 0:
            videos = videos[:video_limit]
        return self._light_videos_iter_type(videos, self)

    def _extract_video_from_response(
        self,
        response: Union[VideoResponse, MobileVideoResponse],
        api_extras: List[APIResponse],
    ):
        if response.video_page.status_code:
            if response.video_page.status_code == 10239:
                raise TikTokAPIError(
                    "Slideshows can't be extracted without mobile emulation."
                )
            raise TikTokAPIError(
                f"Error in video extraction: status code {response.video_page.status_code}"
            )
        video = list(response.item_module.values())[0]

        comments = list(response.comment_item.values()) if response.comment_item else []
        if api_extras:
            for extra in api_extras:
                if extra.comments:
                    comments += extra.comments
        for comment in comments:
            if isinstance(comment.user, LightUser):
                comment.author = self._light_user_getter_type(
                    comment.user.unique_id, self
                )
            else:
                comment.author = self._light_user_getter_type(comment.user, self)

        video.comments = comments
        if not video.comments:
            warnings.warn(
                "Was unable to collect comments.\n"
                "A second attempt or setting a nonzero value for scroll_down_time might work.",
                category=TikTokAPIWarning,
                stacklevel=2,
            )
        if isinstance(video.author, LightUser):
            video.creator = self._light_user_getter_type(video.author.unique_id, self)
        else:
            video.creator = self._light_user_getter_type(video.author, self)

        video.tags = self._create_challenge_iter(video)

        return video

    def _create_challenge_iter(self, video: Video):
        if not video.challenges:
            return self._light_challenge_iter_type([], self)
        return self._light_challenge_iter_type(video.challenges, self)

    def _scroll_page_down(
        self,
        page: Page,
        scroll_down_time: float,
        scroll_down_delay: float,
        scroll_down_iter_delay: float,
    ):
        page.wait_for_timeout(scroll_down_delay * 1000)
        page.evaluate(
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
        page.wait_for_timeout(scroll_down_time * 1000)
        page.evaluate("clearInterval(intervalID)")


__all__ = ["TikTokAPI"]
