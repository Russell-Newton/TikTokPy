"""User account data models"""

from __future__ import annotations

from functools import cached_property
from typing import Any, ForwardRef, Optional, Union
from urllib.parse import quote

from pydantic import AliasChoices, Field, computed_field
from tiktokapipy import TikTokAPIError
from tiktokapipy.models import CamelCaseModel
from tiktokapipy.util.deferred_collectors import DeferredItemListIterator

LightVideo = ForwardRef("LightVideo")
Video = ForwardRef("Video")


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
    id: int = Field(validation_alias=AliasChoices("cid", "uid", "id"))
    """The User's unique id"""
    # short_id: Optional[str]
    nickname: str
    """The User's display name"""

    ########################
    # Security information #
    ########################
    sec_uid: str
    private_account: Optional[bool] = None
    verified: Optional[bool] = None
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

    stats: Optional[UserStats] = None
    """Set on return from API. Contains user statistics."""

    @computed_field(repr=False)
    @property
    def _api(self) -> Any:
        if not hasattr(self, "_api_internal"):
            self._api_internal = None
        return self._api_internal

    @_api.setter
    def _api(self, api):
        self._api_internal = api

    # TODO - Needs msToken cookies or something to work
    @computed_field(repr=False)
    @cached_property
    def videos(self) -> DeferredItemListIterator:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to user._api before collecting videos"
            )
        return DeferredItemListIterator(self._api, "post", self.sec_uid)


del LightVideo, Video


from tiktokapipy.models.video import LightVideo, Video  # noqa E402

User.model_rebuild()


def user_link(user: Union[int, str]) -> str:
    """
    Get a link to extract user data from the user's id or unique username.

    e.g.: ``user_link("tiktok")``

    :param user: The user's unique name (no ``'@'``) or id.
    :return: a link that can be used to scrape data on the User.
    """
    quoted = quote(user)
    return f"https://www.tiktok.com/@{quoted}"
