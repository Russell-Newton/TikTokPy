"""
Challenge (Hashtag) data models
"""

from __future__ import annotations

from functools import cached_property
from typing import Any, ForwardRef, Optional

from pydantic import AliasChoices, Field, computed_field
from tiktokapipy import TikTokAPIError
from tiktokapipy.models import CamelCaseModel
from tiktokapipy.util.deferred_collectors import DeferredItemListIterator

LightVideo = ForwardRef("LightVideo")
Video = ForwardRef("Video")


class ChallengeStats(CamelCaseModel):
    """Stats specific to a Challenge"""

    video_count: int
    view_count: int


class LightChallenge(CamelCaseModel):
    """Bare minimum information for scraping"""

    title: str


class Challenge(LightChallenge):
    """Challenge data"""

    id: int = Field(validation_alias=AliasChoices("cid", "uid", "id"))
    """The Challenge's unique id"""
    desc: str
    is_commerce: Optional[bool] = None
    """Presumably whether this challenge is sponsored."""
    stats: ChallengeStats

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
    def videos(self) -> DeferredItemListIterator:
        if self._api is None:
            raise TikTokAPIError(
                "A TikTokAPI must be attached to challenge._api before collecting videos"
            )
        return DeferredItemListIterator(self._api, "challenge", self.id)


del LightVideo, Video


from tiktokapipy.models.video import LightVideo, Video  # noqa E402

Challenge.model_rebuild()


def challenge_link(challenge: str) -> str:
    """
    Get a link to extract challenge data from its name.

    e.g.: ``challenge_link("fyp")``

    :param challenge: The name of the challenge (no ``'#'``).
    :return: a link that can be used to scrape data on the challenge.
    """
    return f"https://www.tiktok.com/tag/{challenge}"
