import abc
from typing import Dict, Generic, List, Optional, TypeVar, Union

from tiktokapipy.models import CamelCaseModel, TitleCaseModel
from tiktokapipy.models.challenge import Challenge, ChallengeStats
from tiktokapipy.models.comment import Comment
from tiktokapipy.models.user import User, UserStats
from tiktokapipy.models.video import LightVideo, Video


class UserModule(CamelCaseModel):
    users: Dict[str, User]
    stats: Dict[str, UserStats]


class ChallengeInfo(CamelCaseModel):
    challenge: Challenge
    stats: ChallengeStats


class StatusPage(CamelCaseModel):
    status_code: int


class ChallengePage(StatusPage):
    challenge_info: Optional[ChallengeInfo]


class APIResponse(CamelCaseModel):
    status_code: int = 0
    cursor: Optional[int]
    has_more: Union[bool, int]

    total: Optional[int]
    comments: Optional[List[Comment]]
    item_list: Optional[List[LightVideo]]


class PrimaryResponseType(TitleCaseModel):
    pass


class ChallengeResponse(PrimaryResponseType):
    item_module: Optional[Dict[int, LightVideo]]
    challenge_page: ChallengePage


DesktopResponseT = TypeVar("DesktopResponseT")


class MobileResponseMixin(abc.ABC, Generic[DesktopResponseT]):
    @abc.abstractmethod
    def to_desktop(self) -> DesktopResponseT:
        pass


class MobileChallengeResponse(
    PrimaryResponseType, MobileResponseMixin[ChallengeResponse]
):
    mobile_item_module: Optional[Dict[int, LightVideo]]
    mobile_challenge_page: ChallengePage

    def to_desktop(self) -> ChallengeResponse:
        return ChallengeResponse(
            item_module=self.mobile_item_module,
            challenge_page=self.mobile_challenge_page,
        )


class UserResponse(PrimaryResponseType):
    item_module: Optional[Dict[int, LightVideo]]
    user_module: Optional[UserModule]
    user_page: StatusPage


class MobileUserResponse(PrimaryResponseType, MobileResponseMixin[UserResponse]):
    mobile_item_module: Optional[Dict[int, LightVideo]]
    mobile_user_page: StatusPage
    mobile_user_module: Optional[UserModule]

    def to_desktop(self) -> UserResponse:
        return UserResponse(
            item_module=self.mobile_item_module,
            user_page=self.mobile_user_page,
            user_module=self.mobile_user_module,
        )


class VideoResponse(PrimaryResponseType):
    item_module: Optional[Dict[int, Video]]
    comment_item: Optional[Dict[int, Comment]]
    video_page: StatusPage


class MobileVideoData(StatusPage):
    item_info: Optional[Dict[str, Video]]


class MobileVideoModule(CamelCaseModel):
    video_data: MobileVideoData


class MobileVideoResponse(PrimaryResponseType, MobileResponseMixin[VideoResponse]):
    sharing_video_module: MobileVideoModule
    mobile_sharing_comment: APIResponse

    def to_desktop(self) -> VideoResponse:
        return VideoResponse(
            item_module={
                i: v
                for i, v in enumerate(
                    self.sharing_video_module.video_data.item_info.values()
                )
            },
            comment_item={
                comment.id: comment for comment in self.mobile_sharing_comment.comments
            },
            video_page=StatusPage(
                status_code=self.sharing_video_module.video_data.status_code
            ),
        )
