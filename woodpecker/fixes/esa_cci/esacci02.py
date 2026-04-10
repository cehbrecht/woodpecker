from __future__ import annotations

from ..cmip7.cmip702 import CMIP702
from ..registry import FixRegistry


@FixRegistry.register
class ESACCI02(CMIP702):
    code = "ESACCI02"
    name = "ESA CCI ensure project_id is present"
    description = "ESA CCI bridge fix reusing CMIP702 project_id derivation logic."
    priority = 61
    dataset = "ESA-CCI"
