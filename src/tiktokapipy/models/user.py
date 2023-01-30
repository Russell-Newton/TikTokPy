"""User account data models"""

from __future__ import annotations

from typing import Optional, Union
from urllib.parse import quote

from tiktokapipy.models import AsyncDeferredIterator, CamelCaseModel, DeferredIterator


class BioLink(CamelCaseModel):
    link: str
    # risk: int


class UserStats(CamelCaseModel):
    follower_count: int
    following_count: int
    # heart: int
    heart_count: int
    video_count: int
    digg_count: int

    # need_fix: Union[bool, None]   # not sure what this is... collected on videos, not user pages


class LightUser(CamelCaseModel):
    """Bare minimum information for scraping"""

    unique_id: str
    """The User's unique user"""


class User(LightUser):
    ##################
    # Identification #
    ##################
    id: int
    """The User's unique id"""
    # short_id: Optional[str]
    nickname: str
    """The User's display name"""

    ########################
    # Security information #
    ########################
    sec_uid: str
    private_account: Optional[bool]
    verified: Optional[bool]
    # secret: Optional[bool]
    # ftc: Optional[bool]
    # is_under_age_18: Optional[bool]

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
    # create_time: Optional[int]
    # room_id: Optional[str]
    # extra_info: Optional[dict]        # not sure what this is

    stats: Optional[UserStats]
    """Set on return from API. Contains user statistics."""
    videos: Optional[
        Union[
            DeferredIterator[LightVideo, Video],
            AsyncDeferredIterator[LightVideo, Video],
        ]
    ]
    """Set on return from API. Can be iterated over to load :class:`.Video`s."""


from tiktokapipy.models.video import LightVideo, Video  # noqa E402

User.update_forward_refs()


def user_link(user: Union[int, str]) -> str:
    """
    Get a link to extract user data from the user's id or unique username.

    e.g.: ``user_link("tiktok")``

    :param user: The user's unique name (no ``'@'``) or id.
    :return: a link that can be used to scrape data on the User.
    """
    quoted = quote(user)
    return f"https://www.tiktok.com/@{quoted}"
