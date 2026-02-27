"""Fix registry and built-in fixes.

Importing this package registers built-in fixes via side effects.
Third-party projects can define and import their own fix modules to register
additional fixes.
"""

from .registry import Fix, FixRegistry  # noqa: F401

# Import built-in fixes (keeps the project simple and human-scale).
# If the number of built-in fix modules grows, you can switch to lazy imports.
from . import cmip6_fixes  # noqa: F401
