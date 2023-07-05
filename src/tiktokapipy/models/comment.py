"""
Comment data models
"""

from __future__ import annotations

from functools import cached_property
from typing import Any, ForwardRef, Optional, Union

from playwright.async_api import BrowserContext
from pydantic import AliasChoices, Field, computed_field
from tiktokapipy import TikTokAPIError
from tiktokapipy.models import CamelCaseModel
from tiktokapipy.util.deferred_collectors import (
    DeferredUserGetterAsync,
    DeferredUserGetterSync,
)

LightUser = ForwardRef("LightUser")
User = ForwardRef("User")


class ShareInfo(CamelCaseModel):
    """Info related to comment sharing"""

    url: str
    # acl: dict
    content: str = Field(
        ...,
        alias="desc",
        description="The :class:`.Comment`'s content as seen when shared",
    )
    video_title: str = Field(
        ...,
        alias="title",
        description="The title of the :class:`.Video` this is commented under",
    )


class Comment(CamelCaseModel):
    ############################
    # Content and interactions #
    ############################
    user: Union[LightUser, str]
    """
    We don't want to grab anything more than the unique_id so we can generate the lazy user getter.
    :autodoc-skip:
    """
    text: str
    digg_count: int
    # user_digged: int            # liked by you
    reply_comment_total: Optional[int] = None
    author_pin: Optional[bool] = None  # pinned by author
    is_author_digged: bool  # liked by author
    comment_language: str

    ##################
    # Identification #
    ##################
    id: Optional[int] = Field(None, validation_alias=AliasChoices("cid", "uid", "id"))
    """The Comment's unique id"""
    # share_info: ShareInfo   # contains link to video and some extra information
    video_id: int = Field(
        ..., alias="aweme_id", description="The id of the Video this is commented under"
    )
    # reply_id: int
    # reply_to_reply_id: int

    #################################################
    # Misc fields (not sure what most of these are) #
    #################################################
    # create_time: int
    # status: int
    # text_extra: list
    # stick_position: int
    # user_buried: bool
    # no_show: bool
    # collect_stat: int
    # trans_btn_style: int
    # label_list: Optional[list]

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
    def author(self) -> Union[DeferredUserGetterAsync, DeferredUserGetterSync]:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to comment._api before retrieving creator data"
            )
        unique_id = self.user if isinstance(self.user, str) else self.user.unique_id
        if isinstance(self._api.context, BrowserContext):
            return DeferredUserGetterAsync(self._api, unique_id)
        else:
            return DeferredUserGetterSync(self._api, unique_id)


del User, LightUser


from tiktokapipy.models.user import LightUser, User  # noqa E402

Comment.model_rebuild()
