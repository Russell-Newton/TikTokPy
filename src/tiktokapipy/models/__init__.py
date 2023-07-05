"""
Pydantic models used to load and store TikTok data
"""

from __future__ import annotations

from re import sub

from pydantic import BaseModel

# noinspection PyProtectedMember
from pydantic._internal._model_construction import ModelMetaclass


def _to_camel(field: str) -> str:
    # replace _ and - with space, title case, and remove spaces
    field = sub(r"[_\-]+", " ", field).title().replace(" ", "")
    # make first character lowercase
    return field[0].lower() + field[1:]


def _to_title(field: str) -> str:
    # replace _ and - with space, title case, and remove spaces
    field = sub(r"[_\-]+", " ", field).title().replace(" ", "")
    return field


class DataModelDefaultDocumentor(ModelMetaclass):
    """:autodoc-skip:"""

    def __init__(cls, *args):
        if not cls.__doc__:
            cls.__doc__ = f"{cls.__name__} data"
        super().__init__(*args)


class TikTokDataModel(BaseModel, metaclass=DataModelDefaultDocumentor):
    """:autodoc-skip:"""

    def __init_subclass__(cls, **kwargs):
        if not cls.__doc__:
            cls.__doc__ = f"{cls.__name__} model"
            super.__init_subclass__()


class CamelCaseModel(TikTokDataModel):
    """:autodoc-skip:"""

    model_config = dict(
        alias_generator=_to_camel,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class TitleCaseModel(TikTokDataModel):
    """:autodoc-skip:"""

    model_config = dict(
        alias_generator=_to_title,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


__all__ = [
    "CamelCaseModel",
    "TikTokDataModel",
    "TitleCaseModel",
]
