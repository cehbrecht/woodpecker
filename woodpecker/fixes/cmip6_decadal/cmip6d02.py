from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _needs_calendar_fix(dataset: xr.Dataset) -> bool:
    if "time" not in dataset:
        return False
    time_coord = dataset["time"]
    return (
        time_coord.attrs.get("calendar") == "proleptic_gregorian"
        or time_coord.encoding.get("calendar") == "proleptic_gregorian"
    )


def _apply_calendar_fix(dataset: xr.Dataset) -> bool:
    if not _needs_calendar_fix(dataset):
        return False

    changed = False
    time_coord = dataset["time"]
    if time_coord.attrs.get("calendar") == "proleptic_gregorian":
        time_coord.attrs["calendar"] = "standard"
        changed = True
    if time_coord.encoding.get("calendar") == "proleptic_gregorian":
        time_coord.encoding["calendar"] = "standard"
        changed = True
    return changed


@FixRegistry.register
class CMIP6D02(Fix):
    code = "CMIP6D02"
    name = "Decadal calendar normalization"
    description = "Normalizes CMIP6-decadal time calendar from proleptic_gregorian to standard."
    categories = ["metadata", "calendar"]
    priority = 11
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_calendar_fix(dataset):
            return ["time calendar should be normalized from 'proleptic_gregorian' to 'standard'"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_calendar_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_calendar_fix(dataset)
