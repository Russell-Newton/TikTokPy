"""This module contains custom option enumerations.

"""

from ...utility import CustomEnum


class OptionsJsonErrorStrategy(CustomEnum):
    RAISE = "raise"
    COERCE = "coerce"
    WARN = "warn"


class OptionsFieldDocPolicy(CustomEnum):
    BOTH = "both"
    DOCSTRING = "docstring"
    DESCRIPTION = "description"


class OptionsSummaryListOrder(CustomEnum):
    ALPHABETICAL = "alphabetical"
    BYSOURCE = "bysource"
