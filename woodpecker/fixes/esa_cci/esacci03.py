from __future__ import annotations

from ..cmip7.cmip703 import CMIP703
from ..registry import FixRegistry


@FixRegistry.register
class ESACCI03(CMIP703):
    code = "ESACCI03"
    name = "ESA CCI rename temp variable to tas"
    description = "ESA CCI bridge fix reusing CMIP703 temp-to-tas rename logic."
    priority = 62
    dataset = "ESA-CCI"
