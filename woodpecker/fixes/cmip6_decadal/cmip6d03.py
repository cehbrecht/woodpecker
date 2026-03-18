from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _needs_realization_var_fix(dataset: xr.Dataset) -> bool:
    if "realization" in dataset.data_vars:
        return False
    return "realization_index" in dataset.attrs


def _apply_realization_var_fix(dataset: xr.Dataset) -> bool:
    if not _needs_realization_var_fix(dataset):
        return False

    raw_value = dataset.attrs.get("realization_index")
    try:
        realization_value = int(raw_value)
    except (TypeError, ValueError):
        return False

    dataset["realization"] = xr.DataArray(realization_value)
    dataset["realization"].attrs["long_name"] = "realization"
    dataset["realization"].attrs[
        "comment"
    ] = "For more information on the ripf, refer to variant_label and global attributes."
    return True


@FixRegistry.register
class CMIP6D03(Fix):
    code = "CMIP6D03"
    name = "Decadal realization variable"
    description = "Adds realization data variable from realization_index for CMIP6-decadal datasets."
    categories = ["metadata"]
    priority = 12
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_realization_var_fix(dataset):
            return ["realization variable should be added from realization_index"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_realization_var_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_realization_var_fix(dataset)
