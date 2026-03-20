from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _vars_requiring_fillvalue_cleanup(dataset: xr.Dataset) -> list[str]:
    candidates = ("realization", "lon_bnds", "lat_bnds", "time_bnds")
    needs_cleanup = []
    for var_name in candidates:
        if var_name not in dataset:
            continue
        if "_FillValue" in dataset[var_name].encoding:
            needs_cleanup.append(var_name)
    return needs_cleanup


def _apply_fillvalue_encoding_cleanup(dataset: xr.Dataset) -> bool:
    changed = False
    for var_name in _vars_requiring_fillvalue_cleanup(dataset):
        del dataset[var_name].encoding["_FillValue"]
        changed = True
    return changed


@FixRegistry.register
class CMIP6D07(Fix):
    code = "CMIP6D07"
    name = "Decadal _FillValue encoding cleanup"
    description = (
        "Removes stale '_FillValue' encoding entries from realization and bounds variables "
        "in CMIP6-decadal datasets."
    )
    categories = ["encoding", "metadata"]
    priority = 16
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        vars_to_fix = _vars_requiring_fillvalue_cleanup(dataset)
        if not vars_to_fix:
            return []
        return ["_FillValue encoding should be removed from variables: " + ", ".join(vars_to_fix)]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        vars_to_fix = _vars_requiring_fillvalue_cleanup(dataset)
        if not vars_to_fix:
            return False
        if dry_run:
            return True
        return _apply_fillvalue_encoding_cleanup(dataset)
