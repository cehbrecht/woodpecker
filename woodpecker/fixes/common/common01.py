from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .helpers import get_data_unit, is_celsius_unit, target_temperature_variable


def _needs_kelvin_conversion(dataset: xr.Dataset) -> bool:
    variable_name = target_temperature_variable(dataset)
    if not variable_name:
        return False
    return is_celsius_unit(get_data_unit(dataset, variable_name))


def _apply_kelvin_conversion(dataset: xr.Dataset) -> bool:
    variable_name = target_temperature_variable(dataset)
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
class COMMON01(Fix):
    code = "COMMON01"
    name = "Normalize tas-like units to Kelvin"
    description = "Converts tas/temp from Celsius-like units to Kelvin."
    categories = ["metadata", "units"]
    priority = 30
    dataset = None

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_kelvin_conversion(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_kelvin_conversion(dataset):
            return []
        variable_name = target_temperature_variable(dataset)
        return [f"{variable_name} should use Kelvin units (K)"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_kelvin_conversion(dataset):
            return False
        if dry_run:
            return True
        return _apply_kelvin_conversion(dataset)
