"""External CMIP7-style plugin fixes for Woodpecker."""

from .cmip7_0001 import EnsureProjectIdIsPresent  # noqa: F401
from .cmip7_0002 import RenameTempVariableToTas  # noqa: F401
from .cmip7_0003 import ConfigurableCmip7ReformatBridge  # noqa: F401
