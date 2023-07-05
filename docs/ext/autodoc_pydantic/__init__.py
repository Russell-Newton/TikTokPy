"""Contains the extension setup.

"""

from pathlib import Path
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.domains import ObjType

from .directives.autodocumenters import (  # PydanticValidatorDocumenter,; PydanticSettingsDocumenter
    PydanticConfigClassDocumenter,
    PydanticFieldDocumenter,
    PydanticModelDocumenter,
)
from .directives.directives import (
    PydanticConfigClass,
    PydanticField,
    PydanticModel,
    PydanticSettings,
    PydanticValidator,
)
from .directives.options.enums import (
    OptionsFieldDocPolicy,
    OptionsJsonErrorStrategy,
    OptionsSummaryListOrder,
)

__version__ = "1.8.0"

from .events import add_fallback_css_class


def add_css_file(app: Sphinx, exception: Exception):
    """Adds custom css to HTML output."""

    filename = "autodoc_pydantic.css"
    static_path = (Path(app.outdir) / "_static").absolute()
    static_path.mkdir(exist_ok=True, parents=True)
    path_css = Path(__file__).parent.joinpath("css", filename)

    if not (static_path / filename).exists():
        content = path_css.read_text()
        (static_path / filename).write_text(content)


def add_domain_object_types(app: Sphinx):
    """Hack to add object types to already instantiated python domain since
    `add_object_type` currently only works for std domain.

    """

    object_types = app.registry.domain_object_types.setdefault("py", {})

    obj_types_mapping = {
        ("field", "validator", "config"): ("obj", "any"),
        ("model", "settings"): ("obj", "any", "class"),
    }

    for obj_types, roles in obj_types_mapping.items():
        for obj_type in obj_types:
            object_types[f"pydantic_{obj_type}"] = ObjType(obj_type, *roles)


def add_configuration_values(app: Sphinx):
    """Adds all configuration values to sphinx application."""

    stem = "autodoc_pydantic_"
    add = app.add_config_value
    json_strategy = OptionsJsonErrorStrategy.WARN
    summary_list_order = OptionsSummaryListOrder.ALPHABETICAL

    add(f"{stem}config_signature_prefix", "model", True, str)
    add(f"{stem}config_members", True, True, bool)

    add(f"{stem}settings_show_json", True, True, bool)
    add(f"{stem}settings_show_json_error_strategy", json_strategy, True, str)
    add(f"{stem}settings_show_config_member", False, True, bool)
    add(f"{stem}settings_show_config_summary", True, True, bool)
    add(f"{stem}settings_show_validator_members", True, True, bool)
    add(f"{stem}settings_show_validator_summary", True, True, bool)
    add(f"{stem}settings_show_field_summary", True, True, bool)
    add(f"{stem}settings_summary_list_order", summary_list_order, True, str)
    add(f"{stem}settings_hide_paramlist", True, True, bool)
    add(f"{stem}settings_hide_reused_validator", True, True, bool)
    add(f"{stem}settings_undoc_members", True, True, bool)
    add(f"{stem}settings_members", True, True, bool)
    add(f"{stem}settings_member_order", "groupwise", True, str)
    add(f"{stem}settings_signature_prefix", "pydantic settings", True, str)

    add(f"{stem}model_show_json", True, True, bool)
    add(f"{stem}model_show_json_error_strategy", json_strategy, True, str)
    add(f"{stem}model_show_config_member", False, True, bool)
    add(f"{stem}model_show_config_summary", True, True, bool)
    add(f"{stem}model_show_validator_members", True, True, bool)
    add(f"{stem}model_show_validator_summary", True, True, bool)
    add(f"{stem}model_show_field_summary", True, True, bool)
    add(f"{stem}model_summary_list_order", summary_list_order, True, str)
    add(f"{stem}model_hide_paramlist", True, True, bool)
    add(f"{stem}model_hide_reused_validator", True, True, bool)
    add(f"{stem}model_undoc_members", True, True, bool)
    add(f"{stem}model_members", True, True, bool)
    add(f"{stem}model_member_order", "groupwise", True, str)
    add(f"{stem}model_signature_prefix", "pydantic model", True, str)
    add(f"{stem}model_erdantic_figure", False, True, bool)
    add(f"{stem}model_erdantic_figure_collapsed", True, True, bool)

    add(f"{stem}validator_signature_prefix", "validator", True, str)
    add(f"{stem}validator_replace_signature", True, True, bool)
    add(f"{stem}validator_list_fields", False, True, bool)

    add(f"{stem}field_list_validators", True, True, bool)
    add(f"{stem}field_doc_policy", OptionsFieldDocPolicy.BOTH, True, str)
    add(f"{stem}field_show_constraints", True, True, bool)
    add(f"{stem}field_show_alias", True, True, bool)
    add(f"{stem}field_show_default", True, True, bool)
    add(f"{stem}field_show_required", True, True, bool)
    add(f"{stem}field_show_optional", True, True, bool)
    add(f"{stem}field_swap_name_and_alias", False, True, bool)
    add(f"{stem}field_signature_prefix", "field", True, str)

    add(f"{stem}add_fallback_css_class", True, True, bool)


def add_directives_and_autodocumenters(app: Sphinx):
    """Adds custom pydantic directives and autodocumenters to sphinx
    application.

    """

    app.add_directive_to_domain("py", "pydantic_field", PydanticField)
    app.add_directive_to_domain("py", "pydantic_model", PydanticModel)
    app.add_directive_to_domain("py", "pydantic_settings", PydanticSettings)
    app.add_directive_to_domain("py", "pydantic_config", PydanticConfigClass)
    app.add_directive_to_domain("py", "pydantic_validator", PydanticValidator)

    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(PydanticFieldDocumenter)
    app.add_autodocumenter(PydanticModelDocumenter)
    # app.add_autodocumenter(PydanticSettingsDocumenter)
    # app.add_autodocumenter(PydanticValidatorDocumenter)
    app.add_autodocumenter(PydanticConfigClassDocumenter)

    app.connect("object-description-transform", add_fallback_css_class)


def setup(app: Sphinx) -> Dict[str, Any]:
    add_configuration_values(app)
    add_directives_and_autodocumenters(app)
    add_domain_object_types(app)
    app.add_css_file("autodoc_pydantic.css")
    app.connect("build-finished", add_css_file)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
