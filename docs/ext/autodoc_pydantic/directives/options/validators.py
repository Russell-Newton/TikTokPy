"""This module contains custom directive option validator functions."""

from typing import Any, Callable, List, Set, Union

from sphinx.ext.autodoc import ALL


def option_members(arg: Any) -> Union[object, List[str]]:
    """Option validator function used to convert the ``:members:`` option for
    auto directives.

    """

    if isinstance(arg, str):
        sanitized = arg.lower()
        if sanitized == "true":
            return ALL
        elif sanitized == "false":
            return None

    if arg in (None, True):
        return ALL
    elif arg is False:
        return None
    else:
        return [x.strip() for x in arg.split(",") if x.strip()]


def option_one_of_factory(choices: Set[Any]) -> Callable:
    """Option validator factory to create a option validation function which
    allows only one value of given set of provided `choices`.

    """

    def option_func(value: Any):
        if value not in choices:
            raise ValueError(f"Option value has to be on of {choices}")
        return value

    return option_func


def option_default_true(arg: Any) -> bool:
    """Option validator used to define boolean options with default to True if
    no argument is passed.

    """

    if isinstance(arg, bool):
        return arg

    if arg is None:
        return True

    sanitized = arg.strip().lower()

    if sanitized == "true":
        return True
    elif sanitized == "false":
        return False
    else:
        raise ValueError(
            f"Directive option argument '{arg}' is not valid. "
            f"Valid arguments are 'true' or 'false'."
        )


def option_list_like(arg: Any) -> Set[str]:
    """Option validator used to define a set of items."""

    if not arg:
        return set()
    else:
        return {x.strip() for x in arg.split(",")}
