from typing import Iterable, Optional

from tiktokapipy.models import CamelCaseModel


class ChallengeStats(CamelCaseModel):
    video_count: int
    view_count: int


class Challenge(CamelCaseModel):
    id: int
    title: str
    desc: str
    is_commerce: bool
    stats: ChallengeStats

    videos: "Optional[Iterable[Video]]"


from tiktokapipy.models.video import Video  # noqa E402

Challenge.update_forward_refs()


def challenge_link(challenge: str):
    return f"https://www.tiktok.com/tag/{challenge}"
