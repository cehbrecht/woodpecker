"""Fix function registry and built-in fix functions.

Importing this package registers built-in fix functions via side effects.
Third-party projects can define and import their own fix modules to register
additional fix functions.
"""

import woodpecker.identity  # noqa: F401

# Import built-in core fixes.
from . import common  # noqa: F401
from .plugins import load_plugins
from .registry import (  # noqa: F401
    UNPRIORITIZED,
    FixFunction,
    FixFunctionRegistry,
    register_fix_function,
)

# Discover and load third-party fix plugins via entry points.
load_plugins()
