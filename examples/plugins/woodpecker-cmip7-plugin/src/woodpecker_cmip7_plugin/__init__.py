"""External CMIP7-style plugin fixes for Woodpecker."""

from .cmip7_0001 import CMIP7_0001  # noqa: F401
from .cmip7_0002 import CMIP7_0002  # noqa: F401
from .cmip7_0003 import CMIP7_0003  # noqa: F401


def load() -> None:
    """Optional callable entry point target.

    The module import side effects already register fixes.
    """

    return None
