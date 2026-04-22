"""External CMIP7-style plugin fixes for Woodpecker."""

from .cmip7_0001 import EnsureProjectIdIsPresentFix  # noqa: F401
from .cmip7_0002 import RenameTempVariableToTasFix  # noqa: F401
from .cmip7_0003 import ConfigurableCmip7ReformatBridgeFix  # noqa: F401
