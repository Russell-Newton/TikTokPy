import json
import time
from typing import List, Tuple, Type, TypeVar

import requests
from playwright.sync_api import Page, Request, Route, sync_playwright
from tiktokapipy import TikTokAPIError
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

T = TypeVar("T", bound=TikTokDataModel)


def _scroll_page_down(page: Page, scroll_down_time: float):
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
        page_load_time: float = 2,
        scroll_down_time: float = 0,
        headless: bool = None,
        data_dump_file: str = None,
    ):
        if scroll_down_time > 0 and headless:
            raise ValueError("Cannot scroll down with a headless browser")
        self.page_load_time = page_load_time
        self.scroll_down_time = scroll_down_time
        if headless is None:
            self.headless = scroll_down_time == 0
        else:
            self.headless = headless
        self.data_dump_file = data_dump_file

    @property
    def browser(self):
        return self._browser

    @browser.setter
    def browser(self, val):
        raise TikTokAPIError("Cannot change browser instance")

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._browser.close()
        self._playwright.stop()

    def _scrape_data(
        self, link: str, data_model: Type[T]
    ) -> Tuple[T, List[APIResponse]]:
        api_extras = []
        extras_json = []

        def capture_api_extras(route: Route, request: Request):
            r = requests.get(
                request.url,
                headers=request.headers,
                cookies={
                    cookie["name"]: cookie["value"]
                    for cookie in self._context.cookies()
                },
            )
            if len(r.content) > 2:
                extras_json.append(json.loads(r.content.decode("utf-8")))
                api_response = APIResponse.parse_raw(r.content)
                api_extras.append(api_response)
            route.continue_()

        page = self._context.new_page()
        page.route("**/api/challenge/item_list/*", capture_api_extras)
        page.route("**/api/comment/list/*", capture_api_extras)
        page.route("**/api/post/item_list/*", capture_api_extras)

        page.goto(link)

        if self.scroll_down_time > 0:
            _scroll_page_down(page, self.scroll_down_time)

        content = page.content()
        time.sleep(self.page_load_time)

        page.close()

        data = content.split('<script id="SIGI_STATE" type="application/json">')[
            1
        ].split("</script>")[0]

        if self.data_dump_file:
            with open(self.data_dump_file, "w+") as f:
                j = json.loads(data)
                j["extras"] = extras_json
                json.dump(j, f, indent=2)

        response = data_model.parse_raw(data)

        return response, api_extras

    def challenge(self, challenge_name: str) -> Challenge:
        link = challenge_link(challenge_name)
        response, api_extras = self._scrape_data(link, ChallengeResponse)
        challenge = response.challenge_page.challenge_info.challenge
        stats = response.challenge_page.challenge_info.stats
        challenge.stats = stats

        videos = list(response.item_module.values())
        if api_extras:
            videos += [
                video
                for video in [
                    extra.item_list for extra in api_extras if extra.item_list
                ]
            ]
        challenge.videos = LightVideosIter(videos, self)

        return challenge

    def user(self, username: str) -> User:
        link = user_link(username)
        response, api_extras = self._scrape_data(link, UserResponse)
        name, user = list(response.user_module.users.items())[0]
        user.stats = response.user_module.stats[name]

        videos = list(response.item_module.values())
        if api_extras:
            videos += [
                video
                for video in [
                    extra.item_list for extra in api_extras if extra.item_list
                ]
            ]
        user.videos = LightVideosIter(videos, self)

        return user

    def video(self, link: str) -> Video:
        response, api_extras = self._scrape_data(link, VideoResponse)
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
