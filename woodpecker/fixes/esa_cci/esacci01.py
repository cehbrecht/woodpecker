from __future__ import annotations

from ..cmip7.cmip701 import CMIP701
from ..registry import FixRegistry


@FixRegistry.register
class ESACCI01(CMIP701):
    code = "ESACCI01"
    name = "ESA CCI normalize tas-like units to Kelvin"
    description = "ESA CCI bridge fix reusing CMIP701 Celsius-to-Kelvin conversion logic."
    priority = 60
    dataset = "ESA-CCI"
