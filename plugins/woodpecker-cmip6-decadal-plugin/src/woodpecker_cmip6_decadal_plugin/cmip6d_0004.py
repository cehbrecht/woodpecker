from __future__ import annotations

import xarray as xr

from woodpecker.fixes.common.helpers import remove_encoding_key, vars_with_encoding_key
from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import is_cmip6_decadal_netcdf


def _vars_requiring_coordinates_cleanup(dataset: xr.Dataset) -> list[str]:
    candidates = ("realization", "lon_bnds", "lat_bnds", "time_bnds")
    return vars_with_encoding_key(dataset, candidates, "coordinates")


def _apply_coordinates_encoding_cleanup(dataset: xr.Dataset) -> bool:
    return remove_encoding_key(
        dataset,
        _vars_requiring_coordinates_cleanup(dataset),
        "coordinates",
    )


@FixRegistry.register
class DecadalCoordinatesEncodingCleanupFix(Fix):
    local_id = "0004"
    name = "Decadal coordinates encoding cleanup"
    description = (
        "Removes stale 'coordinates' encoding entries from realization and bounds variables "
        "in CMIP6-decadal datasets."
    )
    categories = ["encoding", "metadata"]
    priority = 13
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        vars_to_fix = _vars_requiring_coordinates_cleanup(dataset)
        if not vars_to_fix:
            return []
        return ["coordinates encoding should be removed from variables: " + ", ".join(vars_to_fix)]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        vars_to_fix = _vars_requiring_coordinates_cleanup(dataset)
        if not vars_to_fix:
            return False
        if dry_run:
            return True
        return _apply_coordinates_encoding_cleanup(dataset)
