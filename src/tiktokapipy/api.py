"""
Synchronous API for data scraping
"""

from __future__ import annotations

import json
import traceback
import warnings
from typing import Literal, Optional, Type, TypeVar, Union

from playwright.sync_api import Page, TimeoutError, sync_playwright
from pydantic import ValidationError
from tiktokapipy import ERROR_CODES, TikTokAPIError, TikTokAPIWarning
from tiktokapipy.models.challenge import Challenge
from tiktokapipy.models.raw_data import (
    ChallengePage,
    ChallengeResponse,
    MobileChallengeResponse,
    MobileResponseMixin,
    MobileUserResponse,
    MobileVideoResponse,
    PrimaryResponseType,
    UserResponse,
    VideoResponse,
)
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import Video
from tiktokapipy.util.queries import get_challenge_detail_sync

_DataModelT = TypeVar("_DataModelT", bound=PrimaryResponseType, covariant=True)
"""
Generic used for data scraping.
"""


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
        response = ChallengePage.model_validate(
            get_challenge_detail_sync(challenge_name, self.context)
        )
        return self._extract_challenge_from_response(response)

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
        response = self._scrape_data(
            link,
            self._user_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_user_from_response(response)

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
        response = self._scrape_data(
            link,
            self._video_response_type,
            scroll_down_time,
            scroll_down_delay,
            scroll_down_iter_delay,
        )
        return self._extract_video_from_response(response)

    def _scrape_data(
        self,
        link: str,
        data_model: Type[_DataModelT],
        scroll_down_time: float = None,
        scroll_down_delay: float = None,
        scroll_down_iter_delay: float = None,
    ) -> _DataModelT:
        for _ in range(self.navigation_retries + 1):
            self.context.clear_cookies()
            page: Page = self.context.new_page()
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
                content = page.content()
                page.close()

                data = self._extract_and_dump_data(content, data_model)
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

        return data

    def _extract_and_dump_data(self, page_content: str, data_model: Type[_DataModelT]):
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
                json.dump(j, f, indent=2)

        parsed = data_model.model_validate_json(data)
        if isinstance(parsed, MobileResponseMixin):
            parsed = parsed.to_desktop()
        return parsed

    def _extract_challenge_from_response(
        self,
        response: ChallengePage,
    ):
        if response.status_code:
            raise TikTokAPIError(
                f"Error in challenge extraction: status code {response.status_code} "
                f"({ERROR_CODES[response.user_page.status_code]})"
            )
        challenge = response.challenge_info.challenge
        challenge.stats = response.challenge_info.stats
        challenge._api = self

        return challenge

    def _extract_user_from_response(
        self,
        response: Union[UserResponse, MobileUserResponse],
    ):
        if response.user_page.status_code:
            raise TikTokAPIError(
                f"Error in user extraction: status code {response.user_page.status_code} "
                f"({ERROR_CODES[response.user_page.status_code]})"
            )
        name, user = list(response.user_module.users.items())[0]
        user.stats = response.user_module.stats[name]
        user._api = self

        return user

    def _extract_video_from_response(
        self,
        response: Union[VideoResponse, MobileVideoResponse],
    ):
        if response.video_page.status_code:
            raise TikTokAPIError(
                f"Error in video extraction: status code {response.video_page.status_code} "
                f"({ERROR_CODES[response.user_page.status_code]})"
            )
        video = list(response.item_module.values())[0]
        video._api = self

        return video


__all__ = ["TikTokAPI"]
