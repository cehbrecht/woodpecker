from __future__ import annotations

from ..common.common03 import COMMON03
from ..registry import FixRegistry


@FixRegistry.register
class CMIP703(COMMON03):
    code = "CMIP703"
    name = "Rename temp variable to tas"
    description = "Renames data variable temp to tas when tas is missing."
    priority = 42
    dataset = "CMIP7"
