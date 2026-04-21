from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import is_cmip6_decadal_netcdf

try:
    import cftime
except Exception:  # pragma: no cover
    cftime = None


def _needs_calendar_fix(dataset: xr.Dataset) -> bool:
    if "time" not in dataset:
        return False
    time_coord = dataset["time"]
    if cftime is not None and time_coord.dtype == object and time_coord.size > 0:
        first = time_coord.values.flat[0]
        if isinstance(first, cftime.DatetimeProlepticGregorian):
            return True
    return (
        time_coord.attrs.get("calendar") == "proleptic_gregorian"
        or time_coord.encoding.get("calendar") == "proleptic_gregorian"
    )


def _apply_calendar_fix(dataset: xr.Dataset) -> bool:
    if not _needs_calendar_fix(dataset):
        return False

    changed = False
    time_coord = dataset["time"]

    if cftime is not None and time_coord.dtype == object and time_coord.size > 0:
        values = time_coord.values
        if isinstance(values.flat[0], cftime.DatetimeProlepticGregorian):
            converted = [
                cftime.DatetimeGregorian(
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                    has_year_zero=getattr(value, "has_year_zero", None),
                )
                for value in values
            ]
            new_time = xr.DataArray(converted, dims=time_coord.dims, attrs=dict(time_coord.attrs))
            new_time.encoding = dict(time_coord.encoding)
            dataset["time"] = new_time
            time_coord = dataset["time"]
            changed = True

    if time_coord.attrs.get("calendar") == "proleptic_gregorian":
        time_coord.attrs["calendar"] = "standard"
        changed = True
    if time_coord.encoding.get("calendar") == "proleptic_gregorian":
        time_coord.encoding["calendar"] = "standard"
        changed = True
    return changed


@FixRegistry.register
class DecadalCalendarNormalizationFix(Fix):
    local_id = "0002"
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
