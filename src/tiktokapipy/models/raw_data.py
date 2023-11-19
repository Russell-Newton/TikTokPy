"""
Unprocessed data retrieved directly from TikTok
:autodoc-skip:
"""

from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import AliasPath, Field
from tiktokapipy.models import CamelCaseModel, TitleCaseModel
from tiktokapipy.models.challenge import Challenge, ChallengeStats
from tiktokapipy.models.comment import Comment
from tiktokapipy.models.user import User, UserStats
from tiktokapipy.models.video import LightVideo, Video


class UserModule(CamelCaseModel):
    """:autodoc-skip:"""

    users: Dict[str, User]
    stats: Dict[str, UserStats]


class ChallengeInfo(CamelCaseModel):
    """:autodoc-skip:"""

    challenge: Challenge
    stats: ChallengeStats


class StatusPage(CamelCaseModel):
    """:autodoc-skip:"""

    status_code: int


class ChallengePage(StatusPage):
    """:autodoc-skip:"""

    challenge_info: Optional[ChallengeInfo] = None


class VideoInfo(CamelCaseModel):
    """:autodoc-skip:"""

    video: Video = Field(alias="itemStruct")


class VideoPage(StatusPage):
    """:autodoc-skip:"""

    item_info: Optional[VideoInfo] = None


class APIResponse(CamelCaseModel):
    """:autodoc-skip:"""

    status_code: int = 0
    cursor: Optional[int] = None
    has_more: Union[bool, int] = False

    total: Optional[int] = None
    comments: Optional[List[Comment]] = None
    item_list: Optional[List[LightVideo]] = None


class PrimaryResponseType(TitleCaseModel):
    """:autodoc-skip:"""

    pass


class ChallengeResponse(PrimaryResponseType):
    """:autodoc-skip:"""

    item_module: Optional[Dict[int, LightVideo]] = None
    challenge_page: Optional[ChallengePage] = None


DesktopResponseT = TypeVar("DesktopResponseT")


class UserResponse(PrimaryResponseType):
    """:autodoc-skip:"""

    item_module: Optional[Dict[int, LightVideo]] = None
    user_module: Optional[UserModule] = None
    user_page: StatusPage


class VideoResponse(PrimaryResponseType):
    """:autodoc-skip:"""

    item_module: Optional[Dict[int, Video]] = None
    comment_item: Optional[Dict[int, Comment]] = None
    video_page: StatusPage

    # Preprocess to insert id if needed
    @classmethod
    def model_validate(
        cls,
        obj,
        *,
        strict: Optional[bool] = None,
        from_attributes: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        if "ItemModule" in obj:
            for key in obj["ItemModule"]:
                obj["ItemModule"][key]["id"] = key
                obj["ItemModule"][key]["video"]["id"] = key
        return super().model_validate(
            obj, strict=strict, from_attributes=from_attributes, context=context
        )


class SentToLoginResponse(TitleCaseModel):
    redirect_url: str = Field(
        validation_alias=AliasPath("LoginContextModule", "redirectUrl")
    )
