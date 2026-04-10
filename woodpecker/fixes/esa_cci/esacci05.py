from __future__ import annotations

from ..cmip7.cmip705 import CMIP705
from ..registry import FixRegistry


@FixRegistry.register
class ESACCI05(CMIP705):
    code = "ESACCI05"
    name = "ESA CCI remove coordinate FillValue encodings"
    description = "ESA CCI bridge fix reusing CMIP705 coordinate encoding cleanup logic."
    priority = 64
    dataset = "ESA-CCI"
