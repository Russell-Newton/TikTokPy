"""Video data models"""

from __future__ import annotations

from datetime import datetime
from typing import Awaitable, Callable, List, Optional, Union

from pydantic import Field
from tiktokapipy.models import (
    AsyncDeferredIterator,
    CamelCaseModel,
    DeferredIterator,
    TitleCaseModel,
)


class VideoStats(CamelCaseModel):
    digg_count: int
    share_count: int
    comment_count: int
    play_count: int


class SubtitleData(TitleCaseModel):
    language_id: int
    language_code_name: str
    url: str
    url_expire: int
    format: str
    version: int
    source: str
    # video_subtitle_ID: int
    size: int


class VideoData(CamelCaseModel):
    """Contains data about a downloadable video"""

    id: int
    height: int
    width: int
    duration: int
    ratio: str
    format: Optional[str]
    bitrate: Optional[int]
    # encoded_type: str
    # video_quality: str
    # encode_user_tag: str
    # codec_type: str
    # definition: str
    # subtitle_infos: Optional[List[SubtitleData]]

    ################
    # Video stills #
    ################
    cover: str
    origin_cover: str
    dynamic_cover: str
    share_cover: List[str]
    reflow_cover: str

    ###############
    # Video links #
    ###############
    play_addr: str
    download_addr: str


class MusicData(CamelCaseModel):
    """Contains data about the music within a video"""

    id: int
    title: str
    play_url: str
    author_name: Optional[str]
    duration: int
    original: bool
    album: Optional[str]

    cover_large: str
    cover_medium: str
    cover_thumb: str

    # schedule_search_time: int


class ImageUrlList(CamelCaseModel):
    """
    Contains a list of 3 urls that can be used to access an image. Each URL is different, sometimes only the last will
    be populated.
    """

    url_list: List[str]


class ImageData(CamelCaseModel):
    image_url: ImageUrlList = Field(
        ..., alias="imageURL", description="3 urls that can be used to access the image"
    )
    image_width: int
    image_height: int


class ImagePost(CamelCaseModel):
    images: List[ImageData]
    """All images in the slideshow"""
    cover: ImageData
    """Still image on the video before playing"""
    share_cover: ImageData
    """Still image embedded with a sharing link"""
    title: str


class LightVideo(CamelCaseModel):
    """Bare minimum information for scraping"""

    id: int
    """The unique video ID"""
    # Have this here to sort the iteration.
    stats: VideoStats
    """Stats about the video"""
    create_time: datetime


class Video(LightVideo):
    #####################
    # Content and stats #
    #####################
    desc: str
    """Video description"""
    diversification_labels: Optional[List[str]]
    """Tags/Categories applied to the video"""
    challenges: Optional[List[LightChallenge]]
    """
    We don't want to grab anything more than the title so we can generate the lazy challenge getter.
    :autodoc-skip:
    """
    video: VideoData
    music: MusicData
    # digged: bool
    # item_comment_status: int
    # location_created: Optional[str]
    image_post: Optional[ImagePost]
    """The images in the video if the video is a slideshow"""

    ######################
    # Author information #
    ######################
    author: Union[LightUser, str]
    """
    We don't want to grab anything more than the unique_id so we can generate the lazy user getter.
    :autodoc-skip:
    """
    # nickname: Optional[str]
    # author_id: Optional[int]  # redundant with the lazy author getter
    # author_sec_id: Optional[str]
    # avatar_thumb: Optional[Union[str, dict]]
    # author_stats: "UserStats"

    ##########################
    # Duet/stitching/sharing #
    ##########################
    # stitch_enabled: bool
    # duet_enabled: bool
    # share_enabled: bool
    # private_item: bool
    # duet_info: dict
    # duet_display: int         # display format of duet I think
    # stitch_display: int       # display format of stitch
    # mix_info: Optional[dict]

    ##########################################################
    # Ad and Security info (not sure what most of these are) #
    ##########################################################
    # is_ad: bool
    # ad_authorization: bool
    # ad_label_version: int
    # original_item: bool
    # offical_item: bool                # this is a typo
    # is_activity_item: Optional[bool]
    # secret: bool
    # index_enabled: Optional[bool]
    # show_not_pass: bool

    #################################################
    # Misc fields (not sure what most of these are) #
    #################################################
    # schedule_time: Optional[int]
    # take_down: Optional[int]
    # item_mute: bool
    # text_extra: Optional[list]
    # effect_stickers: Optional[list]
    # stickers_on_item: Optional[list]
    # for_friend: bool
    # vl1: bool

    comments: Optional[List[Comment]]
    """Set on return from API. Contains all :class:`.Comment`s gathered during scraping."""
    creator: Optional[Callable[[], Union[User, Awaitable[User]]]]
    """Set on return from API. Call to retrieve data on the :class:`.User` that created the video."""
    tags: Optional[
        Union[
            DeferredIterator[LightChallenge, Challenge],
            AsyncDeferredIterator[LightChallenge, Challenge],
        ]
    ]
    """Set on return from API. Iterate over to retrieve data on the :class:`.Challenge`s applied to the video."""


from tiktokapipy.models.challenge import Challenge, LightChallenge  # noqa E402
from tiktokapipy.models.comment import Comment  # noqa E402
from tiktokapipy.models.user import LightUser, User, UserStats  # noqa E402

Video.update_forward_refs()


def video_link(video_id: int) -> str:
    """Get a working link to a TikTok video from the video's unique id."""
    return f"https://m.tiktok.com/v/{video_id}"
