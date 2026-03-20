from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import get_data_unit, is_celsius_unit


def _target_variable(dataset: xr.Dataset) -> str | None:
    for candidate in ("tas", "temp"):
        if candidate in dataset.data_vars:
            return candidate
    return None


def _needs_kelvin_conversion(dataset: xr.Dataset) -> bool:
    variable_name = _target_variable(dataset)
    if not variable_name:
        return False
    return is_celsius_unit(get_data_unit(dataset, variable_name))


def _apply_kelvin_conversion(dataset: xr.Dataset) -> bool:
    variable_name = _target_variable(dataset)
    if not variable_name:
        return False

    unit = get_data_unit(dataset, variable_name)
    if not is_celsius_unit(unit):
        return False

    variable = dataset[variable_name]
    variable.data = variable.data + 273.15
    variable.attrs["units"] = "K"
    variable.encoding.pop("units", None)
    return True


@FixRegistry.register
class ESMVAL01(Fix):
    code = "ESMVAL01"
    name = "Normalize tas-like units to Kelvin"
    description = "Prototype ESMVal-style fix: converts tas/temp from Celsius-like units to Kelvin."
    categories = ["metadata", "units"]
    priority = 40
    dataset = "ESMVal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_kelvin_conversion(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_kelvin_conversion(dataset):
            return []
        variable_name = _target_variable(dataset)
        return [f"{variable_name} should use Kelvin units (K) for ESMVal workflows"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_kelvin_conversion(dataset):
            return False
        if dry_run:
            return True
        return _apply_kelvin_conversion(dataset)
