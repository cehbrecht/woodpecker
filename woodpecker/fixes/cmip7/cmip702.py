from __future__ import annotations

from ..common.common02 import COMMON02
from ..registry import FixRegistry


@FixRegistry.register
class CMIP702(COMMON02):
    code = "CMIP702"
    name = "Ensure project_id is present"
    description = "Sets project_id from dataset identifier metadata when missing."
    priority = 41
    dataset = "CMIP7"
