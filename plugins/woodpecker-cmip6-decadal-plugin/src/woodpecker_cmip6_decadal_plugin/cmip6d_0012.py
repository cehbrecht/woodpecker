from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import apply_leadtime_metadata, is_cmip6_decadal_netcdf, leadtime_metadata_invalid


def _needs_leadtime_metadata_fix(dataset: xr.Dataset) -> bool:
    if "leadtime" not in dataset.coords:
        return False
    return leadtime_metadata_invalid(dataset["leadtime"])


def _apply_leadtime_metadata_fix(dataset: xr.Dataset) -> bool:
    if not _needs_leadtime_metadata_fix(dataset):
        return False
    apply_leadtime_metadata(dataset["leadtime"])
    return True


@FixRegistry.register
class CMIP6D_0012(Fix):
    code = "CMIP6D_0012"
    name = "Decadal leadtime metadata normalization"
    description = "Normalizes CMIP6-decadal leadtime metadata (units, long_name, standard_name)."
    categories = ["metadata"]
    priority = 21
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_leadtime_metadata_fix(dataset):
            return ["leadtime metadata should be normalized for CMIP6-decadal datasets"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_leadtime_metadata_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_leadtime_metadata_fix(dataset)
