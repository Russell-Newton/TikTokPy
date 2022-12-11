"""
Comment data models
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional, Union

from pydantic import Field
from tiktokapipy.models import CamelCaseModel


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
    reply_comment_total: Optional[int]
    author_pin: Optional[bool]  # pinned by author
    is_author_digged: bool  # liked by author
    comment_language: str

    ##################
    # Identification #
    ##################
    id: Optional[int]
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

    author: Optional[Callable[[], Union[User, Awaitable[User]]]]
    """Set on return from API. Call to retrieve data on the :class:`.User` that wrote the comment."""


from tiktokapipy.models.user import LightUser, User  # noqa E402

Comment.update_forward_refs()
