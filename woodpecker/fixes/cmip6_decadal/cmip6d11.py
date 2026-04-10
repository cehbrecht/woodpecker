from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _normalized_realization_index(dataset: xr.Dataset) -> int | None:
    raw_value = dataset.attrs.get("realization_index")
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _needs_realization_index_fix(dataset: xr.Dataset) -> bool:
    normalized = _normalized_realization_index(dataset)
    if normalized is None:
        return False
    return dataset.attrs.get("realization_index") != normalized


def _apply_realization_index_fix(dataset: xr.Dataset) -> bool:
    normalized = _normalized_realization_index(dataset)
    if normalized is None:
        return False
    if dataset.attrs.get("realization_index") == normalized:
        return False
    dataset.attrs["realization_index"] = normalized
    return True


@FixRegistry.register
class CMIP6D_0011(Fix):
    code = "CMIP6D_0011"
    name = "Decadal realization_index normalization"
    description = "Normalizes CMIP6-decadal realization_index global attribute to integer type."
    categories = ["metadata"]
    priority = 20
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_realization_index_fix(dataset):
            return ["realization_index should be normalized to integer type"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_realization_index_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_realization_index_fix(dataset)
