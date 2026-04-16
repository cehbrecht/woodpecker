"""Fix registry and built-in fixes.

Importing this package registers built-in fixes via side effects.
Third-party projects can define and import their own fix modules to register
additional fixes.
"""

import woodpecker.identity  # noqa: F401

# Import built-in core fixes.
from . import common  # noqa: F401
from .plugins import load_plugins
from .registry import Fix, FixRegistry, register_fix  # noqa: F401

# Discover and load third-party fix plugins via entry points.
load_plugins()
