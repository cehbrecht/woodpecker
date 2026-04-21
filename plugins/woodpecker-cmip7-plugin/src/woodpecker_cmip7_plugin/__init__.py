"""External CMIP7-style plugin fixes for Woodpecker."""

from .cmip7_0001 import EnsureProjectIdIsPresentFix  # noqa: F401
from .cmip7_0002 import RenameTempVariableToTasFix  # noqa: F401
from .cmip7_0003 import ConfigurableCmip7ReformatBridgeFix  # noqa: F401

# Backward-compatible exports
CMIP7_0001 = EnsureProjectIdIsPresentFix
CMIP7_0002 = RenameTempVariableToTasFix
CMIP7_0003 = ConfigurableCmip7ReformatBridgeFix


def load() -> None:
    """Optional callable entry point target.

    The module import side effects already register fixes.
    """

    return None
