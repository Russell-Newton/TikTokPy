"""This module contains composite helper classes for **autodoc_pydantic**
autodocumenters and directives. They mainly intend to encapsulate the
management of directive options.

"""
import functools
from typing import Any, Optional, Set, Union

from docutils.parsers.rst import Directive
from sphinx.ext.autodoc import ALL, Documenter, Options

from ..utility import NONE


class DirectiveOptions:
    """Composite class providing methods to manage getting and setting
    configuration values from global app configuration and local directive
    options.

    This class is tightly coupled with autodoc pydantic autodocumenters because
    it accesses class attributes of the parent class.

    The documenter class' `option` attribute is sometimes modified in order to
    apply autodoc pydantic's rules (e.g. modifying :members:). Since the
    `option` attribute may be shared between documenter instances (may be a
    bug) in sphinx, an independent copy of the `option` attribute is created
    for every autodoc pydantic autodocumenter. This relates to #21.

    """

    def __init__(self, parent: Union[Documenter, Directive]):
        self.parent = parent
        self.parent.options = Options(self.parent.options)
        self.add_default_options()

    def add_default_options(self):
        """Adds all default options."""

        options = getattr(self.parent, "pyautodoc_set_default_option", [])
        for option in options:
            self.set_default_option(option)

    @staticmethod
    def determine_app_cfg_name(name: str) -> str:
        """Provide full app environment configuration name for given option
        name while converting "-" to "_".

        Parameters
        ----------
        name: str
            Name of the option.

        Returns
        -------
        full_name: str
            Full app environment configuration name.

        """

        sanitized = name.replace("-", "_")

        return f"autodoc_pydantic_{sanitized}"

    def is_available(self, name: str) -> bool:
        """Configurations may be disabled for documentation purposes. If the
        directive option `__doc_disable_except__` exists, it contains the
        only available configurations.

        """

        available = self.parent.options.get("__doc_disable_except__")
        if available is None:
            return True
        else:
            return name in available

    def get_app_cfg_by_name(self, name: str) -> Any:
        """Get configuration value from app environment configuration.
        If `name` does not exist, return NONE.

        """

        config_name = self.determine_app_cfg_name(name)
        return getattr(self.parent.env.config, config_name, NONE)

    def get_value(
        self, name: str, prefix: bool = False, force_availability: bool = False
    ) -> Any:
        """Get option value for given `name`. First, looks for explicit
        directive option values (e.g. :member-order:) which have highest
        priority. Second, if no directive option is given, get the default
        option value provided via the app environment configuration.

        Parameters
        ----------
        name: str
            Name of the option.
        prefix: bool
            If True, add `pyautodoc_prefix` to name.
        force_availability: bool
            It is disabled by default however some default configurations like
            `model-summary-list-order` need to be activated all the time.

        """

        if prefix:
            name = f"{self.parent.pyautodoc_prefix}-{name}"

        if name in self.parent.options:
            return self.parent.options[name]
        elif force_availability or self.is_available(name):
            return self.get_app_cfg_by_name(name)

    def is_false(self, name: str, prefix: bool = False) -> bool:
        """Get option value for given `name`. First, looks for explicit
        directive option values (e.g. :member-order:) which have highest
        priority. Second, if no directive option is given, get the default
        option value provided via the app environment configuration.

        Enforces result to be either True or False.

        Parameters
        ----------
        name: str
            Name of the option.
        prefix: bool
            If True, add `pyautodoc_prefix` to name.

        """

        return self.get_value(name=name, prefix=prefix) is False

    def is_true(self, name: str, prefix: bool = False) -> bool:
        """Get option value for given `name`. First, looks for explicit
        directive option values (e.g. :member-order:) which have highest
        priority. Second, if no directive option is given, get the default
        option value provided via the app environment configuration.

        Enforces result to be either True or False.

        Parameters
        ----------
        name: str
            Name of the option.
        prefix: bool
            If True, add `pyautodoc_prefix` to name.

        """

        return self.get_value(name=name, prefix=prefix) is True

    def set_default_option(self, name: str):
        """Set default option value for given `name` from app environment
        configuration if an explicit directive option was not provided.

        Parameters
        ----------
        name: str
            Name of the option.

        """

        if (name not in self.parent.options) and (self.is_available(name)):
            self.parent.options[name] = self.get_app_cfg_by_name(name)

    def set_members_all(self):
        """Specifically sets the :members: option to ALL if activated via
        app environment settings and not deactivated locally by directive
        option.

        """

        option = self.parent.options.get("members", NONE)
        if option is None or option is False:
            self.parent.options["members"] = []
        elif self.get_app_cfg_by_name("members"):
            self.parent.options["members"] = ALL


class AutoDocOptions(DirectiveOptions):
    """Composite class providing methods to handle getting and setting
    autodocumenter directive option values.

    """

    def __init__(self, *args):
        self._configuration_names: Optional[Set[str]] = None
        super().__init__(*args)
        self.add_pass_through_to_directive()

    @property
    def configuration_names(self) -> Set[str]:
        """Returns all configuration names that exist for `autodoc_pydantic`.

        This is used by :obj:`determine_app_cfg_name` to identify
        configuration names that do not need to be prefixed. This is used when
        options of foreign documenters are accessed (e.g. validator documenter
        needs to read configuration values from field documenter).

        """

        if not self._configuration_names:
            prefix = "autodoc_pydantic_"
            self._configuration_names = {
                config.name.replace(prefix, "")
                for config in self.parent.env.config
                if config.name.startswith(prefix)
            }

        return self._configuration_names

    def determine_app_cfg_name(self, name: str) -> str:
        """Provide full app environment configuration name for given option
        name. It contains some logic to get the correct env configuration name,
        e.g. for pydantic model as follows:

        model-show-field-list -> autodoc_pydantic_model_show_field_list
        undoc-members -> autodoc_pydantic_model_undoc_members
        field-swap-name-and-alias -> autodoc_pydantic_field_swap_name_and_alias

        Parameters
        ----------
        name: str
            Name of the option.

        Returns
        -------
        full_name: str
            Full app environment configuration name.

        """

        sanitized = name.replace("-", "_")

        prefix = self.parent.objtype.split("_")[-1]
        is_not_prefixed = prefix not in sanitized
        is_not_existing = sanitized not in self.configuration_names

        if is_not_prefixed and is_not_existing:
            sanitized = f"{prefix}_{sanitized}"

        return f"autodoc_pydantic_{sanitized}"

    def add_pass_through_to_directive(self):
        """Intercepts documenters `add_directive_header` and adds pass through."""

        func = self.parent.add_directive_header

        pass_through = ["__doc_disable_except__"]
        specific = getattr(self.parent, "pyautodoc_pass_to_directive", [])
        pass_through.extend(specific)

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            for option in pass_through:
                self.pass_option_to_directive(option)

            return result

        self.parent.add_directive_header = wrapped

    def pass_option_to_directive(self, name: str):
        """Pass an autodoc option through to the generated directive."""

        if name in self.parent.options:
            source_name = self.parent.get_sourcename()
            value = self.parent.options[name]

            if isinstance("value", set):
                value = ", ".join(value)

            self.parent.add_line(f"   :{name}: {value}", source_name)
