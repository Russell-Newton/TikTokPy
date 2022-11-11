from typing import Iterable, Optional
from urllib.parse import quote

from tiktokapipy.models import CamelCaseModel


class BioLink(CamelCaseModel):
    link: str
    risk: int


class UserStats(CamelCaseModel):
    follower_count: int
    following_count: int
    # heart: int
    heart_count: int
    video_count: int
    digg_count: int

    # need_fix: Union[bool, None]   # not sure what this is... collected on videos, not user pages


class User(CamelCaseModel):
    ##################
    # Identification #
    ##################
    id: int
    # short_id: Optional[str]
    unique_id: str
    nickname: str

    ########################
    # Security information #
    ########################
    sec_uid: str
    private_account: Optional[bool]
    verified: Optional[bool]
    # secret: Optional[bool]
    # ftc: Optional[bool]
    is_under_age_18: Optional[bool]

    ################
    # Avatar links #
    ################
    # avatar_larger: Optional[str]
    # avatar_medium: Optional[str]
    # avatar_thumb: Optional[Union[str, dict]]

    ##################################################################################
    # User-page specific fields (not collected on users collected from a video link) #
    ##################################################################################
    # relation: Optional[int]
    # open_favorite: Optional[bool]
    # comment_setting: Optional[int]
    # duet_setting: Optional[int]
    # stitch_setting: Optional[int]
    # unique_id_modify_time: Optional[int]
    # is_a_d_virtual: Optional[bool]    # not sure what this is
    # tt_seller: Optional[bool]
    # bio_link: Optional[BioLink]       # contains a link and a risk amount
    # signature: Optional[str]

    ###############
    # Misc fields #
    ###############
    create_time: Optional[int]
    # room_id: Optional[str]
    # extra_info: Optional[dict]        # not sure what this is

    stats: Optional[UserStats]
    videos: "Optional[Iterable[Video]]"


from tiktokapipy.models.video import Video  # noqa E402

User.update_forward_refs()


def user_link(username: str) -> str:
    quoted = quote(username)
    return f"https://www.tiktok.com/@{quoted}"
