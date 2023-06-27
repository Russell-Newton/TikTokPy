"""This module contains various utility functions which are relevant for
autodocumenters and directives.

"""

from typing import List

from docutils.nodes import emphasis
from sphinx.addnodes import pending_xref
from sphinx.environment import BuildEnvironment


class NullType:
    """Helper class to present a Null value which is not the same
    as python's `None`. This represents a missing value, or no
    value at all by convention. It should be used as a singleton.

    """

    def __bool__(self):
        return False


NONE = NullType()


def create_field_href(name: str, ref: str, env: BuildEnvironment) -> pending_xref:
    """Create `pending_xref` node with link to given `reference`."""

    options = {
        "refdoc": env.docname,
        "refdomain": "py",
        "reftype": "obj",
        "reftarget": ref,
    }

    refnode = pending_xref(name, **options)
    classes = ["xref", "py", "%s-%s" % ("py", "obj")]
    refnode += emphasis(name, name, classes=classes)
    return refnode


def remove_node_by_tagname(nodes: List, tagname: str):
    """Removes node from list of `nodes` with given `tagname` in place."""

    for remove in [node for node in nodes if node.tagname == tagname]:
        nodes.remove(remove)
