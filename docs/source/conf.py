# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# Problems with imports? Could try `export PYTHONPATH=$PYTHONPATH:`pwd`` from root project dir...
import os
import sys

sys.path.insert(
    0, os.path.abspath("../../src")
)  # Source code dir relative to this file
sys.path.insert(0, os.path.abspath("../ext"))  # Custom ext dir relative to this file

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TikTokPy"
copyright = "2023, Russell Newton"
author = "Russell Newton"
release = "0.1.11.post1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",
    "sphinx_tabs.tabs",
    "sphinxcontrib.autodoc_pydantic",
    "pydantic_autosummary",
]

templates_path = ["_templates"]
exclude_patterns = []

sphinx_tabs_disable_tab_closing = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_style = "css/custom.css"

html_theme_options = {
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# -- Autodoc configuration ---------------------------------------------------

autosummary_generate = True  # Turn on pydantic_autosummary
autosummary_mock_imports = [  # Prevent certain modules from generating
    "tiktokapipy.models.raw_data",
]
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = (
    False  # Remove "view source code" from top of page (for html, not python)
)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable "expensive" imports for sphinx_autodoc_typehints
nbsphinx_allow_errors = True  # Continue through Jupyter errors
add_module_names = False  # Remove namespaces from class/method signatures

autodoc_default_options = {
    "member-order": "bysource",
}

autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_field_show_alias = False

typehints_defaults = "comma"


def autodoc_skip_member(app, what, name, obj, skip, options):
    if obj.__doc__ and ":autodoc-skip:" in obj.__doc__:
        return True
    return None


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
