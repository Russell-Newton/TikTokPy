"""
Synchronous API for data scraping
"""

import json
import warnings
from typing import List, Literal, Tuple, Type, TypeVar, Union

import playwright.sync_api
from playwright.sync_api import (
    APIRequestContext,
    Page,
    Request,
    Route,
    TimeoutError,
    sync_playwright,
)
from pydantic import ValidationError
from tiktokapipy import TikTokAPIError
from tiktokapipy.models.challenge import Challenge, challenge_link
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

DataModelT = TypeVar("DataModelT", bound=PrimaryResponseType)


class LightVideosIter:
    """
    Utility class to lazy-load videos retrieved under a :class:`.Challenge` or :class:`.User` so they aren't all
    loaded at once.
    :autodoc-skip:
    """

    def __init__(self, videos: List[LightVideo], api: "TikTokAPI"):
        self._videos = videos
        self._api = api

    def fetch_video(self) -> Video:
        video = self._api.video(video_link(self._videos[self.next_up].id))
        self.next_up += 1
        return video

    def __iter__(self) -> "LightVideosIter":
        self.next_up = 0
        return self

    def __next__(self) -> Video:
        if self.next_up == len(self._videos):
            raise StopIteration
        return self.fetch_video()


class LightUserGetter:
    """
    Utility class to lazy-load a user retrieved under a :class:`.Comment` or :class:`.Video` so they aren't all loaded
    at once.
    :autodoc-skip:
    """

    def __init__(self, user: str, api: "TikTokAPI"):
        self._user = LightUser(unique_id=user)
        self._api = api

    def __call__(self) -> User:
        return self._api.user(self._user.unique_id)


class TikTokAPI:
    """Synchronous API used to scrape data from TikTok"""

    def __init__(
        self,
        *,
        wait_until: Literal[
            "domcontentloaded", "load", "networkidle", "commit"
        ] = "load",
        scroll_down_time: float = 0,
        headless: bool = None,
        data_dump_file: str = None,
        emulate_mobile: bool = False,
        navigation_timeout: float = 0,
        navigation_retries: int = 0,
        **context_kwargs,
    ):
        """
        :param wait_until: When navigating to a page, when should navigation be considered done?
        :param scroll_down_time: How much time (in seconds) should the page navigation include scrolling down. This can
            load more content from the page. Incompatible with ``headless=True``. Set to 0 to not scroll down.
        :param headless: Whether to use headless browsing. Headless browsing is incompatible with non-zero
            ``scroll_down_time``. Set to ``None`` to have this be determined by ``scroll_down_time``.
        :param data_dump_file: If the data scraped from TikTok should also be dumped to a JSON file before parsing,
            specify the name of the dump file (exluding '.json').
        :param emulate_mobile: Whether to emulate a mobile device during sraping. Required for retrieving data
            on slideshows.
        :param navigation_timeout: How long (in milliseconds) page navigation should wait before timing out. Set to 0 to
            disable the timeout.
        :param navigation_retries: How many times to retry navigation if ``network_timeout`` is exceeded. Set to 0 to
            not retry navigation.
        :param context_kwargs: Any extra kwargs used to initialize the playwright browser context.
        """
        if scroll_down_time > 0 and headless:
            raise ValueError("Cannot scroll down with a headless browser")
        self.wait_until = wait_until
        self.scroll_down_time = scroll_down_time
        if headless is None:
            self.headless = scroll_down_time == 0
        else:
            self.headless = headless
        self.data_dump_file = data_dump_file
        self.emulate_mobile = emulate_mobile
        self.context_kwargs = context_kwargs
        self.navigation_timeout = navigation_timeout * 1000
        self.navigation_retries = navigation_retries

    def __enter__(self) -> "TikTokAPI":
        self._playwright = sync_playwright().start()

        self._browser = self.playwright.chromium.launch(headless=self.headless)

        context_kwargs = self.context_kwargs

        if self.emulate_mobile:
            context_kwargs.update(self.playwright.devices["iPhone 12"])
        else:
            context_kwargs.update(self.playwright.devices["Desktop Edge"])

        self._context = self.browser.new_context(**context_kwargs)
        if self.navigation_timeout > 0:
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
    def _light_videos_iter_type(self):
        return LightVideosIter

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

    def challenge(self, challenge_name: str, video_limit: int = 0) -> Challenge:
        """
        Retrieve data on a :class:`.Challenge` (hashtag) from TikTok. Only up to the ``video_limit`` most recent videos
        will be retrievable by the scraper.

        :param challenge_name: The name of the challenge. e.g.: ``"fyp"``
        :param video_limit: The max number of recent videos to retrieve. Set to 0 for no limit
        :return: A :class:`.Challenge` object containing the scraped data
        :rtype: :class:`.Challenge`
        """
        link = challenge_link(challenge_name)
        response, api_extras = self._scrape_data(link, self._challenge_response_type)
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    def user(self, user: Union[int, str], video_limit: int = 0) -> User:
        """
        Retrieve data on a :class:`.User` from TikTok. Only up to the ``video_limit`` most recent videos will be
        retrievable by the scraper.

        :param user: The unique user or id of the user. e.g.: for @tiktok, use ``"tiktok"``
        :param video_limit: The max number of recent videos to retrieve. Set to 0 for no limit
        :return: A :class:`.User` object containing the scraped data
        :rtype: :class:`.User`
        """
        link = user_link(user)
        response, api_extras = self._scrape_data(link, self._user_response_type)
        return self._extract_user_from_response(response, api_extras, video_limit)

    def video(self, link: str) -> Video:
        """
        Retrieve data on a :class:`.Video` from TikTok. If the video is a slideshow, :attr:`.emulate_mobile` must be
        set to ``True`` at API initialization or this method will raise a :exc:`TikTokAPIError`.

        :param link: The link to the video. Can be found from a unique video id with :func:`.video_link`.
        :return: A :class:`.Video` object containing the scraped data
        :rtype: :class:`.Video`
        """
        response, api_extras = self._scrape_data(link, self._video_response_type)
        return self._extract_video_from_response(response, api_extras)

    def _scrape_data(
        self, link: str, data_model: Type[DataModelT]
    ) -> Tuple[DataModelT, List[APIResponse]]:
        api_extras: List[APIResponse] = []
        extras_json: List[dict] = []

        def capture_api_extras(route: Route, request: Request):
            request_context: APIRequestContext = self.context.request
            try:
                response: playwright.sync_api.APIResponse = request_context.get(
                    request.url, headers=request.headers
                )
            except Exception:
                route.abort()
                return
            body = response.body()
            if len(body) > 2:
                _data = response.json()
                extras_json.append(_data)
                api_response = APIResponse.parse_obj(_data)
                api_extras.append(api_response)
            route.fulfill(
                status=response.status,
                headers=response.headers,
                body=body,
                response=response,
            )

        for _ in range(self.navigation_retries + 1):
            self.context.clear_cookies()
            page: Page = self.context.new_page()
            page.route("**/api/challenge/item_list/*", capture_api_extras)
            page.route("**/api/comment/list/*", capture_api_extras)
            page.route("**/api/post/item_list/*", capture_api_extras)
            try:
                page.goto(link, wait_until=self.wait_until)

                if self.scroll_down_time > 0:
                    self._scroll_page_down(page)

                content = page.content()
                page.close()

                data = self._extract_and_dump_data(content, extras_json, data_model)
            except (TimeoutError, ValidationError, IndexError):
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
        self, page_content: str, extras_json: List[dict], data_model: Type[DataModelT]
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
        challenge.videos = self._create_videos_iter(response, api_extras, video_limit)

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
        user.videos = self._create_videos_iter(response, api_extras, video_limit)

        return user

    def _create_videos_iter(
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
                "Was unable to collect comments.\nA second attempt might work."
            )
        if isinstance(video.author, LightUser):
            video.creator = self._light_user_getter_type(video.author.unique_id, self)
        else:
            video.creator = self._light_user_getter_type(video.author, self)

        return video

    def _scroll_page_down(self, page: Page):
        page.evaluate(
            """
            var intervalID = setInterval(function () {
                var scrollingElement = (document.scrollingElement || document.body);
                scrollingElement.scrollTop = scrollingElement.scrollHeight;
            }, 500);
            """
        )
        page.wait_for_timeout(self.scroll_down_time * 1000)
        page.evaluate("clearInterval(intervalID)")


__all__ = ["TikTokAPI"]
