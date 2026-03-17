from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_netcdf, lower_source_name


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
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal time metadata"
    description = "Ensures CMIP6-decadal time coordinate has long_name='valid_time'."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        findings = []
        if "decadal" not in lower_source_name(dataset):
            findings.append("expected CMIP6 decadal filename hint ('decadal') is missing")
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
