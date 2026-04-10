from __future__ import annotations

from ..common.common04 import COMMON04
from ..registry import FixRegistry


@FixRegistry.register
class CMIP704(COMMON04):
    code = "CMIP704"
    name = "Ensure latitude is increasing"
    description = "Flips datasets with decreasing latitude coordinates to increasing order."
    priority = 43
    dataset = "CMIP7"
