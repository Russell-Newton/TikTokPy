"""Video data models"""

# Import statements and other initial setups
from __future__ import annotations
from datetime import datetime
from functools import cached_property
from typing import Any, ForwardRef, List, Optional, Union
from pydantic import validator, Field, computed_field

from playwright.async_api import BrowserContext as AsyncBrowserContext
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

# VideoStats model
class VideoStats(CamelCaseModel):
    digg_count: int
    share_count: int
    comment_count: int
    play_count: int
    collect_count: int

# SubtitleData model
class SubtitleData(TitleCaseModel):
    language_id: Optional[int] = Field(alias='LanguageID')
    language_code_name: str = Field(alias='LanguageCodeName')
    url: str = Field(alias='Url')
    url_expire: int = Field(alias='UrlExpire')
    format: str = Field(alias='Format')
    version: int = Field(alias='Version')
    source: str = Field(alias='Source')
    size: int = Field(alias='Size')

# VideoData model with adjustments
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
    subtitle_infos: Optional[List[SubtitleData]]
    cover: str
    origin_cover: str
    dynamic_cover: Optional[str] = None
    share_cover: Optional[List[str]] = None
    reflow_cover: Optional[str] = None
    play_addr: Optional[str] = None
    download_addr: Optional[str] = None

# MusicData model
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

# ImageUrlList model
class ImageUrlList(CamelCaseModel):
    url_list: List[str]

# ImageData model
class ImageData(CamelCaseModel):
    image_url: ImageUrlList = Field(
        ..., alias="imageURL", description="3 urls that can be used to access the image"
    )
    image_width: int
    image_height: int

# ImagePost model
class ImagePost(CamelCaseModel):
    images: List[ImageData]
    cover: ImageData
    share_cover: ImageData
    title: Optional[str] = None

# LightVideo model
class LightVideo(CamelCaseModel):
    id: int = Field(alias="id")
    stats: VideoStats
    create_time: datetime

# Video model with adjustments
class Video(LightVideo):
    desc: str
    diversification_labels: Optional[List[str]]
    challenges: Optional[List[LightChallenge]]
    video: VideoData
    music: MusicData
    digged: bool
    item_comment_status: int
    author: Union[LightUser, str]

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
            raise TikTokAPIError("A TikTokAPI must be attached to video._api before collecting comments")
        return DeferredCommentIterator(self._api, self.id)

    @computed_field(repr=False)
    @cached_property
    def tags(self) -> DeferredChallengeIterator:
        if self._api is None:
            raise TikTokAPIError("A TikTokAPI must be attached to video._api before collecting tags")
        return DeferredChallengeIterator(
            self._api,
            [challenge.title for challenge in self.challenges] if self.challenges else [],
        )

    @computed_field(repr=False)
    @cached_property
    def creator(self) -> Union[DeferredUserGetterAsync, DeferredUserGetterSync]:
        if self._api is None:
            raise TikTokAPIError("A TikTokAPI must be attached to video._api before retrieving creator data")
        unique_id = self.author if isinstance(self.author, str) else self.author.unique_id
        if isinstance(self._api.context, AsyncBrowserContext):
            return DeferredUserGetterAsync(self._api, unique_id)
        else:
            return DeferredUserGetterSync(self._api, unique_id)

    @computed_field(repr=False)
    @cached_property
    def url(self) -> str:
        return video_link(self.id)

# Utility functions
def video_link(video_id: int) -> str:
    return f"https://m.tiktok.com/v/{video_id}"

def is_mobile_share_link(link: str) -> bool:
    import re
    return re.match(r"https://vm\.tiktok\.com/[0-9A-Za-z]*", link) is not None

# Re-imports at the end of the file (circular dependency resolution)
del Challenge, LightChallenge, Comment, LightUser, User, UserStats
from src.tiktokapipy.models.challenge import Challenge, LightChallenge  # noqa E402
from src.tiktokapipy.models.comment import Comment  # noqa E402
from src.tiktokapipy.models.user import LightUser, User, UserStats  # noqa E402

# Rebuild models if necessary
Video.model_rebuild()



def video_link(video_id: int) -> str:
    """Get a working link to a TikTok video from the video's unique id."""
    return f"https://m.tiktok.com/v/{video_id}"


def is_mobile_share_link(link: str) -> bool:
    import re

    return re.match(r"https://vm\.tiktok\.com/[0-9A-Za-z]*", link) is not None
