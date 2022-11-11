from typing import Dict, List, Optional

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


class ChallengePage(CamelCaseModel):
    challenge_info: ChallengeInfo


class RawResponse(TitleCaseModel):
    item_module: Dict[int, Video]
    user_module: Optional[UserModule]
    comment_item: Optional[Dict[int, Comment]]
    challenge_page: Optional[ChallengePage]


class APIResponse(CamelCaseModel):
    status_code: int
    cursor: int
    has_more: int

    total: Optional[int]
    comments: Optional[List[Comment]]
    item_list: Optional[List[LightVideo]]


class ChallengeResponse(TitleCaseModel):
    item_module: Dict[int, LightVideo]
    challenge_page: ChallengePage


class UserResponse(TitleCaseModel):
    item_module: Dict[int, LightVideo]
    user_module: UserModule


class VideoResponse(TitleCaseModel):
    item_module: Dict[int, Video]
    comment_item: Optional[Dict[int, Comment]]
