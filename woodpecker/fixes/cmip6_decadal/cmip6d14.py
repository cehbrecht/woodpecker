from __future__ import annotations

import numpy as np
import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf
from .common import extract_start_year as _extract_start_year

try:
    import cftime
except Exception:  # pragma: no cover
    cftime = None


def _target_calendar(dataset: xr.Dataset) -> str:
    if "time" in dataset:
        return (
            str(dataset["time"].encoding.get("calendar") or dataset["time"].attrs.get("calendar") or "standard")
            .strip()
            .lower()
        )
    return "standard"


def _build_reftime_value(dataset: xr.Dataset) -> object | None:
    year = _extract_start_year(dataset)
    if year is None:
        return None
    cal = _target_calendar(dataset)
    if cftime is not None:
        calendar_factory = {
            "standard": cftime.DatetimeGregorian,
            "gregorian": cftime.DatetimeGregorian,
            "proleptic_gregorian": cftime.DatetimeProlepticGregorian,
            "360_day": cftime.Datetime360Day,
            "365_day": cftime.DatetimeNoLeap,
            "noleap": cftime.DatetimeNoLeap,
            "366_day": cftime.DatetimeAllLeap,
            "all_leap": cftime.DatetimeAllLeap,
        }.get(cal)
        if calendar_factory is not None:
            return calendar_factory(year, 11, 1)
    return np.datetime64(f"{year:04d}-11-01")


def _needs_reftime_fix(dataset: xr.Dataset) -> bool:
    target = _build_reftime_value(dataset)
    if target is None:
        return False
    if "reftime" not in dataset.coords:
        return True
    current = dataset["reftime"]
    if current.ndim != 0:
        return True
    if current.values.item() != target:
        return True
    if current.attrs.get("long_name") != "Start date of the forecast":
        return True
    if current.attrs.get("standard_name") != "forecast_reference_time":
        return True
    return False


def _apply_reftime_fix(dataset: xr.Dataset) -> bool:
    target = _build_reftime_value(dataset)
    if target is None:
        return False

    dataset = dataset
    reftime = xr.DataArray(target)
    reftime.attrs["long_name"] = "Start date of the forecast"
    reftime.attrs["standard_name"] = "forecast_reference_time"
    reftime.encoding["dtype"] = "int32"
    reftime.encoding["units"] = "days since 1850-01-01"
    reftime.encoding["calendar"] = _target_calendar(dataset)

    dataset.coords["reftime"] = reftime
    return True


@FixRegistry.register
class CMIP6D14(Fix):
    code = "CMIP6D14"
    name = "Decadal reftime coordinate"
    description = "Adds or normalizes CMIP6-decadal scalar reftime coordinate and metadata."
    categories = ["metadata", "structure"]
    priority = 23
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_reftime_fix(dataset):
            return ["reftime coordinate should be added or normalized from decadal start token"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_reftime_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_reftime_fix(dataset)