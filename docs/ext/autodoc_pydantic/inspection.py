"""This module contains the inspection functionality for pydantic models. It
is used to retrieve relevant information about fields, validators, config and
schema of pydantical models.

"""
import inspect
import itertools
import pydoc
import warnings
from collections import defaultdict
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pydantic
from _decimal import Decimal
from pydantic import BaseModel, create_model
from pydantic._internal._utils import lenient_issubclass
from pydantic.fields import FieldInfo
from sphinx.addnodes import desc_signature

ASTERISK_FIELD_NAME = "all fields"


numeric_types = (int, float, Decimal)
_str_types_attrs: Tuple[Tuple[str, Union[type, Tuple[type, ...]], str], ...] = (
    ("max_length", numeric_types, "maxLength"),
    ("min_length", numeric_types, "minLength"),
    ("regex", str, "pattern"),
)

_numeric_types_attrs: Tuple[Tuple[str, Union[type, Tuple[type, ...]], str], ...] = (
    ("gt", numeric_types, "exclusiveMinimum"),
    ("lt", numeric_types, "exclusiveMaximum"),
    ("ge", numeric_types, "minimum"),
    ("le", numeric_types, "maximum"),
    ("multiple_of", numeric_types, "multipleOf"),
)


def get_field_schema_validations(field: FieldInfo) -> Dict[str, Any]:
    """
    Get the JSON Schema validation keywords for a ``field`` with an annotation of
    a Pydantic ``FieldInfo`` with validation arguments.
    """
    f_schema: Dict[str, Any] = {}

    if lenient_issubclass(field.annotation, Enum):
        # schema is already updated by `enum_process_schema`; just update with field extra
        return f_schema

    if lenient_issubclass(field.annotation, (str, bytes)):
        for attr_name, t, keyword in _str_types_attrs:
            attr = getattr(field, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    if lenient_issubclass(field.annotation, numeric_types) and not issubclass(
        field.annotation, bool
    ):
        for attr_name, t, keyword in _numeric_types_attrs:
            attr = getattr(field, attr_name, None)
            if isinstance(attr, t):
                f_schema[keyword] = attr
    return f_schema


class ValidatorAdapter(BaseModel):
    """Provide standardized interface to pydantic's validator objects with
    additional metadata (e.g. root validator) for internal usage in
    autodoc_pydantic.

    """

    func: Callable
    root_pre: bool = False
    root_post: bool = False

    @property
    def name(self) -> str:
        """Return the validators function name."""
        return self.func.__name__

    @property
    def class_name(self) -> Optional[str]:
        """Return the validators class name. It might be None if validator
        is not bound to a class.

        """

        qualname = self.func.__qualname__.split(".")
        if len(qualname) > 1:
            return qualname[-2]

    @property
    def module(self) -> str:
        """Return the validators module name."""

        return self.func.__module__

    @property
    def object_path(self) -> str:
        """Return the fully qualified object path of the validators function."""

        return f"{self.func.__module__}.{self.func.__qualname__}"

    def is_member(self, model: Type) -> bool:
        """Check if `self.func` is a member of provided `model` class or its
        base classes. This can be used to identify functions that are reused
        as validators.

        """

        if self.class_name is None:
            return False

        bases = (f"{x.__module__}.{x.__qualname__}" for x in model.__mro__)
        return f"{self.module}.{self.class_name}" in bases

    class Config:
        arbitrary_types_allowed = True

    def __hash__(self):
        return id(f"{self}")


class ValidatorFieldMap(NamedTuple):
    """Contains single mapping of a pydantic validator and field."""

    field_name: str
    """Name of the field."""

    validator_name: str
    """Name of the validator."""

    field_ref: str
    """Reference to field."""

    validator_ref: str
    """Reference to validataor."""


class BaseInspectionComposite:
    """Serves as base class for inspector composites which are coupled to
    `ModelInspector` instances. Each composite provides a separate namespace to
    handle different areas of pydantic models (e.g. fields and validators).

    """

    def __init__(self, parent: "ModelInspector"):
        self._parent: "ModelInspector" = parent
        self.model = self._parent.model


class FieldInspector(BaseInspectionComposite):
    """Provide namespace for inspection methods for fields of pydantic models."""

    def __init__(self, parent: "ModelInspector"):
        super().__init__(parent)
        self.attribute = self.model.__fields__

    @property
    def names(self) -> List[str]:
        """Return field names while keeping ordering."""

        return list(self.attribute.keys())

    def get(self, name: str):
        """Get the instance of `ModelField` for given field `name`."""

        return self.attribute[name]

    def get_alias_or_name(self, field_name: str) -> str:
        """Get the alias of a pydantic field if given. Otherwise, return the
        field name.

        """

        if field_name == ASTERISK_FIELD_NAME:
            return field_name

        alias = self.get(field_name).alias
        if alias is not None:
            return alias
        else:
            return field_name

    def get_property_from_field_info(self, field_name: str, property_name: str) -> Any:
        """Get specific property value from pydantic's field info."""

        field = self.get(field_name)
        return getattr(field, property_name, None)

    def get_constraints(self, field_name: str) -> Dict[str, Any]:
        """Get constraints for given `field_name`."""

        field = self.get(field_name)
        constraints = get_field_schema_validations(field)
        ignore = {"env_names", "env"}

        # ignore additional kwargs from pydantic `Field`, see #110
        extra_kwargs = self.get_property_from_field_info(
            field_name=field_name, property_name="extra"
        )
        if extra_kwargs:
            ignore = ignore.union(extra_kwargs.keys())

        return {key: value for key, value in constraints.items() if key not in ignore}

    def is_required(self, field_name: str) -> bool:
        """Check if a given pydantic field is required/mandatory. Returns True,
        if a value for this field needs to provided upon model creation.

        """

        return self.get(field_name).is_required()

    def has_default_factory(self, field_name: str) -> bool:
        """Check if field has a `default_factory` being set. This information
        is used to determine if a pydantic field is optional or not.

        """

        return self.get(field_name).default_factory is not None

    def is_json_serializable(self, field_name: str) -> bool:
        """Check if given pydantic field is JSON serializable by calling
        pydantic's `model.schema()` method. Custom objects might not be
        serializable and hence would break JSON schema generation.

        """

        field = self.get(field_name)
        return self._is_json_serializable(field)

    @classmethod
    def _is_json_serializable(cls, field):
        """Ensure JSON serializability for given pydantic `ModelField`."""

        # check for sub fields in case of `Union` or alike, see #98
        # if field.sub_fields:
        #     return all(
        #         cls._is_json_serializable(sub_field)
        #         for sub_field in field.sub_fields
        #     )

        # hide user warnings in sphinx output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return cls._test_field_serializabiltiy(field)

    @staticmethod
    def _test_field_serializabiltiy(field) -> bool:
        """Test JSON serializability for given pydantic `ModelField`."""

        class Cfg:
            arbitrary_types_allowed = True

        try:
            field_args = (field.type_, field.default)
            model = create_model("_", test_field=field_args, Config=Cfg)
            model.schema()
            return True

        except Exception:
            return False

    @property
    def non_json_serializable(self) -> List[str]:
        """Get all fields that can't be safely JSON serialized."""

        return [name for name in self.names if not self.is_json_serializable(name)]

    def __bool__(self):
        """Equals to False if no fields are present."""

        return bool(self.attribute)


'''
class ValidatorInspector(BaseInspectionComposite):
    """Provide namespace for inspection methods for validators of pydantic
    models.

    """

    def __init__(self, parent: 'ModelInspector'):
        super().__init__(parent)
        self.attribute: Dict[str, List] = self.model.__validators__

    @property
    def values(self) -> Set[ValidatorAdapter]:
        """Returns set of all available validators.

        """

        all_validators = self._parent.field_validator_mappings.values()
        flattened = itertools.chain.from_iterable(all_validators)
        return set(flattened)

    def get_reused_validator_method_names(self) -> List[str]:
        """Identify all bound methods names that are used to generate reused
        validators as placeholders.

        """

        reused_validators = self.get_reused_validators()
        if not reused_validators:
            return []

        validator_set = set([x.func for x in reused_validators])
        bound_methods = {key: value
                         for key, value in vars(self.model).items()
                         if inspect.ismethod(getattr(self.model, key))}

        return [key for key, value in bound_methods.items()
                if value.__func__ in validator_set]

    def get_reused_validators(self) -> List[ValidatorAdapter]:
        """Identify all reused validators.

        """

        return [validator for validator in self.values
                if not validator.is_member(self.model)]

    @property
    def names(self) -> Set[str]:
        """Return names of all validators of pydantic model.

        """

        return set([validator.name for validator in self.values])

    def __bool__(self):
        """Equals to False if no validators are present.

        """

        return bool(self.attribute)
'''


class ConfigInspector(BaseInspectionComposite):
    """Provide namespace for inspection methods for config class of pydantic
    models.

    """

    def __init__(self, parent: "ModelInspector"):
        super().__init__(parent)
        self.attribute: Dict = self.model.Config

    @property
    def is_configured(self) -> bool:
        """Check if pydantic model config was explicitly configured. If not,
        it defaults to the standard configuration provided by pydantic and
        typically does not required documentation.

        """

        cfg = self.attribute

        is_main_config = cfg is pydantic.main.BaseConfig
        is_setting_config = cfg is pydantic.env_settings.BaseSettings.Config
        is_default_config = is_main_config or is_setting_config

        return not is_default_config

    @property
    def items(self) -> Dict:
        """Return all non private (without leading underscore `_`) items of
        pydantic configuration class.

        """

        return {
            key: getattr(self.attribute, key)
            for key in dir(self.attribute)
            if not key.startswith("_")
        }


class ReferenceInspector(BaseInspectionComposite):
    """Provide namespace for inspection methods for creating references
    mainly between pydantic fields and validators.

    Importantly, `mappings` provides the set of all `ValidatorFieldMap`
    instances which contain all references between fields and validators.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mappings = self._create_mappings()

    @property
    def model_path(self) -> str:
        """Retrieve the full path of the model."""

        return f"{self.model.__module__}.{self.model.__name__}"

    def create_model_reference(self, name: str) -> str:
        """Create reference for given attribute `name` returning full path
        including the model path.

        """

        return f"{self.model_path}.{name}"

    def _create_mappings(self) -> Set[ValidatorFieldMap]:
        """Generate reference mappings between validators and corresponding
        fields.

        """
        mappings = set()

        for field, validators in self._parent.field_validator_mappings.items():
            if field == "*":
                field_name = ASTERISK_FIELD_NAME
            else:
                field_name = field

            for validator in validators:
                mapping = ValidatorFieldMap(
                    field_name=field_name,
                    field_ref=f"{self.model_path}.{field_name}",
                    validator_name=validator.name,
                    validator_ref=validator.object_path,
                )
                mappings.add(mapping)

        return mappings

    def filter_by_validator_name(self, name: str) -> List[ValidatorFieldMap]:
        """Return mappings for given validator `name`."""

        return [mapping for mapping in self.mappings if mapping.validator_name == name]

    def filter_by_field_name(self, name: str) -> List[ValidatorFieldMap]:
        """Return mappings for given field `name`."""

        return [
            mapping
            for mapping in self.mappings
            if mapping.field_name in (name, ASTERISK_FIELD_NAME)
        ]


class SchemaInspector(BaseInspectionComposite):
    """Provide namespace for inspection methods for general properties of
    pydantic models.

    """

    @property
    def sanitized(self) -> Dict:
        """Get model's `schema` while handling non serializable fields. Such
        fields will be replaced by TypeVars.

        """

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return self.model.schema()

        except (TypeError, ValueError):
            new_model = self.create_sanitized_model()
            return new_model.schema()

    def create_sanitized_model(self) -> BaseModel:
        """Generates a new pydantic model from the original one while
        substituting invalid fields with typevars.

        """

        invalid_fields = self._parent.fields.non_json_serializable
        new = {name: (TypeVar(name), None) for name in invalid_fields}
        return create_model(self.model.__name__, __base__=self.model, **new)


class StaticInspector:
    """Namespace under `ModelInspector` for static methods."""

    @staticmethod
    def is_pydantic_model(obj: Any) -> bool:
        """Determine if object is a valid pydantic model."""

        try:
            return issubclass(obj, BaseModel)
        except TypeError:
            return False

    @classmethod
    def is_pydantic_field(cls, parent: Any, field_name: str) -> bool:
        """Determine if given `field` is a pydantic field."""

        if not cls.is_pydantic_model(parent):
            return False

        return field_name in parent.__fields__

    @classmethod
    def is_validator_by_name(cls, name: str, obj: Any) -> bool:
        """Determine if a validator is present under provided `name` for given
        `model`.

        """

        if cls.is_pydantic_model(obj):
            inspector = ModelInspector(obj)
            return name in inspector.validators.names
        return False


class ModelInspector:
    """Provides inspection functionality for pydantic models."""

    static = StaticInspector

    def __init__(self, model: Type[BaseModel]):
        self.model = model
        self.field_validator_mappings = self.get_field_validator_mapping()

        # self.config = ConfigInspector(self)
        self.schema = SchemaInspector(self)
        self.fields = FieldInspector(self)
        # self.validators = ValidatorInspector(self)
        self.references = ReferenceInspector(self)

    def get_field_validator_mapping(self) -> Dict[str, List[ValidatorAdapter]]:
        """Collect all available validators keyed by their corresponding
        fields including post/pre root validators.

        Validators are wrapped into `ValidatorAdapters` to provide uniform
        interface within autodoc_pydantic.

        """

        mapping = defaultdict(list)

        # standard validators
        # for field, validators in self.model.__validators__.items():
        #     for validator in validators:
        #         mapping[field].append(ValidatorAdapter(func=validator.func))
        #
        # # root pre
        # for func in self.model.__pre_root_validators__:
        #     mapping["*"].append(ValidatorAdapter(func=func,
        #                                          root_pre=True))
        #
        # # root post
        # for _, func in self.model.__post_root_validators__:
        #     mapping["*"].append(ValidatorAdapter(func=func,
        #                                          root_post=True))

        return mapping

    @classmethod
    def from_child_signode(cls, signode: desc_signature) -> "ModelInspector":
        """Create instance from a child `signode` as used within sphinx
        directives.

        """

        model_path_parts = signode["fullname"].split(".")[:-1]
        model_path = ".".join(model_path_parts)
        model = pydoc.locate(f"{signode['module']}.{model_path}")

        if not cls.static.is_pydantic_model(model):
            raise ValueError(
                f"Signode with full name {signode['fullname']} and extracted "
                f"model path does reference pydantic model. "
            )

        return cls(model)
