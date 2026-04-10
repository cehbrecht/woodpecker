from __future__ import annotations

from ..common.common05 import COMMON05
from ..registry import FixRegistry


@FixRegistry.register
class CMIP705(COMMON05):
    code = "CMIP705"
    name = "Remove coordinate FillValue encodings"
    description = "Removes _FillValue encoding entries from common coordinate variables."
    priority = 44
    dataset = "CMIP7"
