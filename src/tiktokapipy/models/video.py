from typing import Awaitable, Callable, List, Optional, Union

from tiktokapipy.models import CamelCaseModel, TitleCaseModel


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
    id: int
    height: int
    width: int
    duration: int
    ratio: str
    format: str
    bitrate: int
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
    id: int
    title: str
    play_url: str
    author_name: str
    duration: int
    original: bool
    album: str

    cover_large: str
    cover_medium: str
    cover_thumb: str

    # schedule_search_time: int


class LightVideo(CamelCaseModel):
    id: int


class Video(LightVideo):
    #####################
    # Content and stats #
    #####################
    desc: str
    stats: VideoStats
    diversification_labels: Optional[List[str]]  # video categories/tags
    challenges: "Optional[List[Challenge]]"  # hashtags
    video: VideoData  # contains video file information, subtitle info, and download links
    music: MusicData  # contains sound/bg music information and download links
    # digged: bool                               # liked by you
    # item_comment_status: int
    location_created: Optional[str]

    ######################
    # Author information #
    ######################
    author: "Union[User, str]"
    nickname: Optional[str]
    author_id: Optional[int]
    # author_sec_id: Optional[str]
    # avatar_thumb: Optional[Union[str, dict]]
    author_stats: "UserStats"

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
    is_ad: bool
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
    # create_time: int
    # schedule_time: Optional[int]
    # take_down: Optional[int]
    # item_mute: bool
    # text_extra: Optional[list]
    # effect_stickers: Optional[list]
    # stickers_on_item: Optional[list]
    # for_friend: bool
    # vl1: bool

    comments: "Optional[List[Comment]]"
    creator: "Optional[Callable[[], Union[User, Awaitable[User]]]]"


from tiktokapipy.models.challenge import Challenge  # noqa E402
from tiktokapipy.models.comment import Comment  # noqa E402
from tiktokapipy.models.user import User, UserStats  # noqa E402

Video.update_forward_refs()


def video_link(_id: int):
    return f"https://m.tiktok.com/v/{_id}"
