from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _needs_realization_long_name_fix(dataset: xr.Dataset) -> bool:
    if "realization" not in dataset.data_vars:
        return False
    return dataset["realization"].attrs.get("long_name") != "realization"


def _apply_realization_long_name_fix(dataset: xr.Dataset) -> bool:
    if not _needs_realization_long_name_fix(dataset):
        return False
    dataset["realization"].attrs["long_name"] = "realization"
    return True


@FixRegistry.register
class CMIP6D10(Fix):
    code = "CMIP6D10"
    name = "Decadal realization long_name normalization"
    description = "Normalizes realization long_name metadata to 'realization' for CMIP6-decadal datasets."
    categories = ["metadata"]
    priority = 19
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_realization_long_name_fix(dataset):
            return ["realization long_name should be normalized to 'realization'"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_realization_long_name_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_realization_long_name_fix(dataset)