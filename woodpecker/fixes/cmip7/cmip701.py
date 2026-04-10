from __future__ import annotations

from ..common.common01 import COMMON01
from ..registry import FixRegistry


@FixRegistry.register
class CMIP701(COMMON01):
    code = "CMIP701"
    name = "Normalize tas-like units to Kelvin"
    description = "Converts tas/temp from Celsius-like units to Kelvin."
    priority = 40
    dataset = "CMIP7"
