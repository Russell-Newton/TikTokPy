"""
Pydantic models used to load and store TikTok data
"""

import json
from re import sub
from typing import Union

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


__all__ = ["CamelCaseModel", "TikTokDataModel", "TitleCaseModel"]
