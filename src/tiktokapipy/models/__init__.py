"""
Pydantic models used to load and store TikTok data
"""

from __future__ import annotations

import json
from abc import abstractmethod
from re import sub
from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    Protocol,
    TypeVar,
    Union,
    runtime_checkable,
)

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

from pydantic import BaseModel
from pydantic.main import ModelMetaclass


def _sub_id_recursive(obj: Union[dict, list]):
    if isinstance(obj, dict):
        if "id" not in obj:
            if "cid" in obj:
                obj["id"] = obj["cid"]
                del obj["cid"]
            if "uid" in obj:
                obj["id"] = obj["uid"]
                del obj["uid"]
        for sub_obj in obj.values():
            if isinstance(sub_obj, dict) or isinstance(sub_obj, list):
                _sub_id_recursive(sub_obj)
    else:
        for sub_obj in obj:
            if isinstance(sub_obj, dict) or isinstance(sub_obj, list):
                _sub_id_recursive(sub_obj)


def _load_with_id_alias(v):
    obj = json.loads(v)
    _sub_id_recursive(obj)
    return obj


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

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True
        json_loads = _load_with_id_alias


class TitleCaseModel(TikTokDataModel):
    """:autodoc-skip:"""

    class Config:
        alias_generator = _to_title
        allow_population_by_field_name = True
        json_loads = _load_with_id_alias


_DeferredIterInT = TypeVar("_DeferredIterInT", bound=TikTokDataModel)
_DeferredIterOutT = TypeVar("_DeferredIterOutT", bound=TikTokDataModel)


@runtime_checkable
class DeferredIterator(Protocol[_DeferredIterInT, _DeferredIterOutT]):
    """:autodoc-skip:"""

    light_models: Iterable[_DeferredIterInT]

    def __iter__(self) -> DeferredIterator[_DeferredIterInT, _DeferredIterOutT]:
        ...

    def __next__(self) -> _DeferredIterOutT:
        ...

    @abstractmethod
    def fetch(self, idx: int) -> _DeferredIterOutT:
        ...

    def sorted_by(
        self, key: Callable[[_DeferredIterInT], SupportsLessThan], reverse: bool = False
    ) -> DeferredIterator[_DeferredIterInT, _DeferredIterOutT]:
        ...

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


@runtime_checkable
class AsyncDeferredIterator(Protocol[_DeferredIterInT, _DeferredIterOutT]):
    """:autodoc-skip:"""

    light_models: Iterable[_DeferredIterInT]

    def __aiter__(self) -> DeferredIterator[_DeferredIterInT, _DeferredIterOutT]:
        ...

    async def __anext__(self) -> _DeferredIterOutT:
        ...

    @abstractmethod
    async def fetch(self, idx: int) -> _DeferredIterOutT:
        ...

    def sorted_by(
        self, key: Callable[[_DeferredIterInT], SupportsLessThan], reverse: bool = False
    ) -> DeferredIterator[_DeferredIterInT, _DeferredIterOutT]:
        ...

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v


__all__ = [
    "CamelCaseModel",
    "TikTokDataModel",
    "TitleCaseModel",
    "DeferredIterator",
    "AsyncDeferredIterator",
]
