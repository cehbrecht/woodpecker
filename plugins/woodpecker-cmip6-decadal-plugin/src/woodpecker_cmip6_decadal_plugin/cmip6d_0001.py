from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import is_cmip6_decadal_netcdf


def _needs_time_long_name_fix(dataset: xr.Dataset) -> bool:
    if "time" not in dataset:
        return False
    return dataset["time"].attrs.get("long_name") != "valid_time"


def _apply_time_long_name_fix(dataset: xr.Dataset) -> bool:
    if not _needs_time_long_name_fix(dataset):
        return False
    dataset["time"].attrs["long_name"] = "valid_time"
    return True


@FixRegistry.register
class CMIP6D_0001(Fix):
    code = "CMIP6D_0001"
    name = "Decadal time metadata"
    description = "Ensures CMIP6-decadal time coordinate has long_name='valid_time'."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        findings = []
        if _needs_time_long_name_fix(dataset):
            findings.append("time coordinate long_name should be 'valid_time'")
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        needs_change = _needs_time_long_name_fix(dataset)
        if not needs_change:
            return False

        if dry_run:
            return True

        return _apply_time_long_name_fix(dataset)
