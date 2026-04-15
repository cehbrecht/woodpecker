"""Fix registry and built-in fixes.

Importing this package registers built-in fixes via side effects.
Third-party projects can define and import their own fix modules to register
additional fixes.
"""

import woodpecker.identity  # noqa: F401

# Import built-in fixes (keeps the project simple and human-scale).
# If the number of built-in fix modules grows, you can switch to lazy imports.
from . import (
    atlas,  # noqa: F401
    cmip6,  # noqa: F401
    cmip6_decadal,  # noqa: F401
    common,  # noqa: F401
)
from .plugins import load_plugins
from .registry import Fix, FixRegistry, register_fix  # noqa: F401

# Discover and load third-party fix plugins via entry points.
load_plugins()
