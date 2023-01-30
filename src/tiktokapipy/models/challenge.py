"""
Challenge (Hashtag) data models
"""

from __future__ import annotations

from typing import Optional, Union

from tiktokapipy.models import AsyncDeferredIterator, CamelCaseModel, DeferredIterator


class ChallengeStats(CamelCaseModel):
    """Stats specific to a Challenge"""

    video_count: int
    view_count: int


class LightChallenge(CamelCaseModel):
    """Bare minimum information for scraping"""

    title: str


class Challenge(LightChallenge):
    """Challenge data"""

    id: int
    """The Challenge's unique id"""
    desc: str
    is_commerce: Optional[bool]
    """Presumably whether this challenge is sponsored."""
    stats: ChallengeStats

    videos: Optional[
        Union[
            DeferredIterator[LightVideo, Video],
            AsyncDeferredIterator[LightVideo, Video],
        ]
    ]
    """Set on return from API. Can be iterated over to load :class:`.Video`s."""


from tiktokapipy.models.video import LightVideo, Video  # noqa E402

Challenge.update_forward_refs()


def challenge_link(challenge: str) -> str:
    """
    Get a link to extract challenge data from its name.

    e.g.: ``challenge_link("fyp")``

    :param challenge: The name of the challenge (no ``'#'``).
    :return: a link that can be used to scrape data on the challenge.
    """
    return f"https://www.tiktok.com/tag/{challenge}"
