"""Video data models"""

# Import statements and other initial setups
from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import Any, ForwardRef, List, Optional, Union

from playwright.async_api import BrowserContext as AsyncBrowserContext
from pydantic import AliasChoices, Field, computed_field
from tiktokapipy import TikTokAPIError
from tiktokapipy.models import CamelCaseModel, TitleCaseModel
from tiktokapipy.util.deferred_collectors import (
    DeferredChallengeIterator,
    DeferredCommentIterator,
    DeferredUserGetterAsync,
    DeferredUserGetterSync,
)

# Forward references for model dependencies
LightChallenge = ForwardRef("LightChallenge")
Challenge = ForwardRef("Challenge")
Comment = ForwardRef("Comment")
LightUser = ForwardRef("LightUser")
User = ForwardRef("User")
UserStats = ForwardRef("UserStats")


class VideoStats(CamelCaseModel):
    digg_count: int
    share_count: int
    comment_count: int
    play_count: int
    collect_count: int


class SubtitleData(TitleCaseModel):
    language_id: Optional[int] = Field(alias="LanguageID", default=None)
    language_code_name: str = Field(alias="LanguageCodeName")
    url: str = Field(alias="Url")
    url_expire: int = Field(alias="UrlExpire")
    format: str = Field(alias="Format")
    version: int = Field(alias="Version")
    source: str = Field(alias="Source")
    size: int = Field(alias="Size")


class VideoData(CamelCaseModel):
    height: int
    width: int
    duration: int
    ratio: str
    format: Optional[str] = None
    bitrate: Optional[int] = None
    encoded_type: Optional[str] = None
    video_quality: Optional[str] = None
    encode_user_tag: Optional[str] = None
    codec_type: Optional[str] = None
    definition: Optional[str] = None
    subtitle_infos: Optional[List[SubtitleData]] = None
    cover: str
    origin_cover: str
    dynamic_cover: Optional[str] = None
    share_cover: Optional[List[str]] = None
    reflow_cover: Optional[str] = None
    play_addr: Optional[str] = None
    download_addr: Optional[str] = None


class MusicData(CamelCaseModel):
    id: int
    title: str
    play_url: Optional[str] = None
    author_name: Optional[str] = None
    duration: Optional[int] = None
    original: bool
    album: Optional[str] = None
    cover_large: str
    cover_medium: str
    cover_thumb: str


class ImageUrlList(CamelCaseModel):
    url_list: List[str]


class ImageData(CamelCaseModel):
    image_url: ImageUrlList = Field(
        ..., alias="imageURL", description="3 urls that can be used to access the image"
    )
    image_width: int
    image_height: int


class ImagePost(CamelCaseModel):
    images: List[ImageData]
    cover: ImageData
    share_cover: ImageData
    title: Optional[str] = None


class LightVideo(CamelCaseModel):
    id: int = Field(validation_alias=AliasChoices("cid", "uid", "id"))
    stats: VideoStats
    create_time: datetime


class Video(LightVideo):
    desc: str
    diversification_labels: Optional[List[str]] = None
    challenges: Optional[List[LightChallenge]] = None
    video: VideoData
    music: MusicData
    digged: bool
    item_comment_status: int
    author: Union[LightUser, str]
    image_post: Optional[ImagePost] = None
    """The images in the video if the video is a slideshow"""

    @computed_field(repr=False)
    @property
    def _api(self) -> Any:
        if not hasattr(self, "_api_internal"):
            self._api_internal = None
        return self._api_internal

    @_api.setter
    def _api(self, api):
        self._api_internal = api

    @computed_field(repr=False)
    @cached_property
    def comments(self) -> DeferredCommentIterator:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to video._api before collecting comments"
            )
        return DeferredCommentIterator(self._api, self.id)

    @computed_field(repr=False)
    @cached_property
    def tags(self) -> DeferredChallengeIterator:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to video._api before collecting tags"
            )
        return DeferredChallengeIterator(
            self._api,
            [challenge.title for challenge in self.challenges]
            if self.challenges
            else [],
        )

    @computed_field(repr=False)
    @cached_property
    def creator(self) -> Union[DeferredUserGetterAsync, DeferredUserGetterSync]:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to video._api before retrieving creator data"
            )
        unique_id = (
            self.author if isinstance(self.author, str) else self.author.unique_id
        )
        if isinstance(self._api.context, AsyncBrowserContext):
            return DeferredUserGetterAsync(self._api, unique_id)
        else:
            return DeferredUserGetterSync(self._api, unique_id)

    @computed_field(repr=False)
    @cached_property
    def url(self) -> str:
        return video_link(self.id)

    def download(self) -> str:
        """
        Downloads this video, returning the relative filepath where it was stored.
        Requires yt-dlp installed (``pip install yt-dlp``
        or ``pip install tiktokapipy[download]``)
        """
        if self.image_post:
            raise TikTokAPIError(
                "The download function isn't available for slideshows."
            )

        try:
            import yt_dlp
        except ImportError:
            raise TikTokAPIError(
                "You don't have youtube_dl installed! "
                "Please install with `pip install yt-dlp` or "
                "`pip install tiktokapipy[download]"
            )

        downloaded_file = ""

        class GetFileNamePP(yt_dlp.postprocessor.PostProcessor):
            def run(self, info):
                nonlocal downloaded_file
                downloaded_file = info["filename"]
                return [], info

        with yt_dlp.YoutubeDL() as ydl:
            ydl.add_post_processor(GetFileNamePP())
            ydl.download([video_link(self.id)])

        return downloaded_file


del Challenge, LightChallenge, Comment, LightUser, User, UserStats
from tiktokapipy.models.challenge import Challenge, LightChallenge  # noqa E402
from tiktokapipy.models.comment import Comment  # noqa E402
from tiktokapipy.models.user import LightUser, User, UserStats  # noqa E402

Video.model_rebuild()


def video_link(video_id: int) -> str:
    """Get a working link to a TikTok video from the video's unique id."""
    return f"https://m.tiktok.com/v/{video_id}"


def is_mobile_share_link(link: str) -> bool:
    import re

    return re.match(r"https://vm\.tiktok\.com/[0-9A-Za-z]*", link) is not None
