from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf
from .common import normalized_start_token as _normalized_start_token


def _needs_start_token_fix(dataset: xr.Dataset) -> bool:
    normalized = _normalized_start_token(dataset)
    if not normalized:
        return False
    return (
        dataset.attrs.get("startdate") != normalized
        or dataset.attrs.get("sub_experiment_id") != normalized
    )


def _apply_start_token_fix(dataset: xr.Dataset) -> bool:
    normalized = _normalized_start_token(dataset)
    if not normalized:
        return False

    changed = False
    if dataset.attrs.get("startdate") != normalized:
        dataset.attrs["startdate"] = normalized
        changed = True
    if dataset.attrs.get("sub_experiment_id") != normalized:
        dataset.attrs["sub_experiment_id"] = normalized
        changed = True
    return changed


@FixRegistry.register
class CMIP6D09(Fix):
    code = "CMIP6D09"
    name = "Decadal start token normalization"
    description = (
        "Normalizes CMIP6-decadal startdate and sub_experiment_id to the canonical sYYYY11 token."
    )
    categories = ["metadata"]
    priority = 18
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_start_token_fix(dataset):
            return ["startdate and sub_experiment_id should be normalized to sYYYY11"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_start_token_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_start_token_fix(dataset)
