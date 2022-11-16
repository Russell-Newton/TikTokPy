import json
import time
from typing import List, Literal, Tuple, Type, TypeVar, Union

import requests
from playwright.sync_api import Page, Request, Route, sync_playwright
from tiktokapipy.models import TikTokDataModel
from tiktokapipy.models.challenge import Challenge, challenge_link
from tiktokapipy.models.raw_data import (
    APIResponse,
    ChallengeResponse,
    UserResponse,
    VideoResponse,
)
from tiktokapipy.models.user import User, user_link
from tiktokapipy.models.video import LightVideo, Video, video_link

DataModelT = TypeVar("DataModelT", bound=TikTokDataModel)


class TikTokAPIError(Exception):
    pass


class LightVideosIter:
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


class TikTokAPI:
    def __init__(
        self,
        wait_until: Literal[
            "domcontentloaded", "load", "networkidle", "commit"
        ] = "networkidle",
        scroll_down_time: float = 0,
        headless: bool = None,
        data_dump_file: str = None,
        emulate_mobile: bool = False,
        **context_kwargs
    ):
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

    def __enter__(self):
        self._playwright = sync_playwright().start()

        self._browser = self.playwright.chromium.launch(headless=self.headless)

        context_kwargs = self.context_kwargs
        if self.emulate_mobile:
            context_kwargs.update(self.playwright.devices["iPhone 12"])
        self._context = self.browser.new_context(**context_kwargs)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    @property
    def playwright(self):
        if not hasattr(self, "_playwright"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._playwright

    @property
    def browser(self):
        if not hasattr(self, "_browser"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._browser

    @property
    def context(self):
        if not hasattr(self, "_context"):
            raise TikTokAPIError("TikTokAPI must be used as a context manager")
        return self._context

    @property
    def light_videos_iter_type(self):
        return LightVideosIter

    def challenge(self, challenge_name: str, video_limit: int = 25) -> Challenge:
        link = challenge_link(challenge_name)
        response, api_extras = self._scrape_data(link, ChallengeResponse)
        return self._extract_challenge_from_response(response, api_extras, video_limit)

    def user(self, username: str, video_limit: int = 25) -> User:
        link = user_link(username)
        response, api_extras = self._scrape_data(link, UserResponse)
        return self._extract_user_from_response(response, api_extras, video_limit)

    def video(self, link: str) -> Video:
        response, api_extras = self._scrape_data(link, VideoResponse)
        return self._extract_video_from_response(response, api_extras)

    def _scrape_data(
        self, link: str, data_model: Type[DataModelT]
    ) -> Tuple[DataModelT, List[APIResponse]]:
        api_extras: List[APIResponse] = []
        extras_json: List[dict] = []

        def capture_api_extras(route: Route, request: Request):
            r = requests.get(
                request.url,
                headers=request.headers,
                cookies={
                    cookie["name"]: cookie["value"] for cookie in self.context.cookies()
                },
            )
            if len(r.content) > 2:
                extras_json.append(json.loads(r.content.decode("utf-8")))
                api_response = APIResponse.parse_raw(r.content)
                api_extras.append(api_response)
            route.continue_()

        page = self.context.new_page()
        page.route("**/api/challenge/item_list/*", capture_api_extras)
        page.route("**/api/comment/list/*", capture_api_extras)
        page.route("**/api/post/item_list/*", capture_api_extras)

        page.goto(link, wait_until=self.wait_until)

        if self.scroll_down_time > 0:
            self._scroll_page_down(page, self.scroll_down_time)

        content = page.content()

        page.close()

        return self._extract_and_dump_data(content, extras_json, data_model), api_extras

    def _extract_and_dump_data(
        self, page_content: str, extras_json: List[dict], data_model: Type[DataModelT]
    ):
        data = page_content.split('<script id="SIGI_STATE" type="application/json">')[
            1
        ].split("</script>")[0]

        if self.data_dump_file:
            with open(self.data_dump_file, "w+") as f:
                j = json.loads(data)
                j["extras"] = extras_json
                json.dump(j, f, indent=2)

        return data_model.parse_raw(data)

    def _extract_challenge_from_response(
        self,
        response: ChallengeResponse,
        api_extras: List[APIResponse],
        video_limit: int = 25,
    ):
        challenge = response.challenge_page.challenge_info.challenge
        stats = response.challenge_page.challenge_info.stats
        challenge.stats = stats
        challenge.videos = self._create_videos_iter(response, api_extras, video_limit)

        return challenge

    def _extract_user_from_response(
        self,
        response: UserResponse,
        api_extras: List[APIResponse],
        video_limit: int = 25,
    ):
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
            videos += [
                video
                for video in [
                    extra.item_list for extra in api_extras if extra.item_list
                ]
            ]
        if video_limit > 0:
            videos = videos[:video_limit]
        return self.light_videos_iter_type(videos, self)

    def _extract_video_from_response(
        self, response: VideoResponse, api_extras: List[APIResponse]
    ):
        video = list(response.item_module.values())[0]

        comments = list(response.comment_item.values()) if response.comment_item else []
        if api_extras:
            comments += [
                comment
                for comment in [
                    extra.comments for extra in api_extras if extra.comments
                ]
            ]
        video.comments = comments

        return video

    def _scroll_page_down(self, page: Page, scroll_down_time: float):
        page.evaluate(
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
        time.sleep(scroll_down_time)

        page.evaluate("clearInterval(intervalID)")
