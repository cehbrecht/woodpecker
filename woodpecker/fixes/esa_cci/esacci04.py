from __future__ import annotations

from ..cmip7.cmip704 import CMIP704
from ..registry import FixRegistry


@FixRegistry.register
class ESACCI04(CMIP704):
    code = "ESACCI04"
    name = "ESA CCI ensure latitude is increasing"
    description = "ESA CCI bridge fix reusing CMIP704 latitude-order normalization logic."
    priority = 63
    dataset = "ESA-CCI"
