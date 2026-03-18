from __future__ import annotations

import numpy as np
import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf
from .common import apply_leadtime_metadata, leadtime_metadata_invalid

try:
    import cftime
except Exception:  # pragma: no cover
    cftime = None


def _derive_leadtime_days(dataset: xr.Dataset) -> np.ndarray | None:
    if "time" not in dataset.coords or "reftime" not in dataset.coords:
        return None

    time_vals = np.asarray(dataset["time"].values)
    if time_vals.size == 0:
        return np.array([], dtype=np.float64)

    ref_value = np.asarray(dataset["reftime"].values).item()

    if np.issubdtype(time_vals.dtype, np.datetime64):
        time64 = time_vals.astype("datetime64[ns]")
        ref64 = np.asarray(ref_value).astype("datetime64[ns]")
        return ((time64 - ref64) / np.timedelta64(1, "D")).astype(np.float64)

    if np.issubdtype(time_vals.dtype, np.number):
        return (time_vals.astype(np.float64) - float(ref_value)).astype(np.float64)

    if cftime is not None and hasattr(time_vals.flat[0], "calendar"):
        calendar = getattr(time_vals.flat[0], "calendar", "standard")
        units = (
            f"days since {ref_value.year:04d}-{ref_value.month:02d}-{ref_value.day:02d} "
            f"{ref_value.hour:02d}:{ref_value.minute:02d}:{ref_value.second:02d}"
        )
        return np.asarray(
            cftime.date2num(time_vals.tolist(), units=units, calendar=calendar), dtype=np.float64
        )

    return None


def _leadtime_metadata_invalid(dataset: xr.Dataset) -> bool:
    if "leadtime" not in dataset.coords:
        return True
    return leadtime_metadata_invalid(dataset["leadtime"])


def _leadtime_values_invalid(dataset: xr.Dataset, target: np.ndarray) -> bool:
    if "leadtime" not in dataset.coords:
        return True
    current = np.asarray(dataset["leadtime"].values)
    if current.shape != target.shape:
        return True
    return not np.allclose(current.astype(np.float64), target, equal_nan=True)


def _needs_leadtime_fix(dataset: xr.Dataset) -> bool:
    target = _derive_leadtime_days(dataset)
    if target is None:
        return False
    return _leadtime_metadata_invalid(dataset) or _leadtime_values_invalid(dataset, target)


def _apply_leadtime_fix(dataset: xr.Dataset) -> bool:
    target = _derive_leadtime_days(dataset)
    if target is None:
        return False

    dataset.coords["leadtime"] = ("time", target.astype(np.float64))
    leadtime = dataset["leadtime"]
    apply_leadtime_metadata(leadtime)
    leadtime.encoding["dtype"] = "double"
    return True


@FixRegistry.register
class CMIP6D15(Fix):
    code = "CMIP6D15"
    name = "Decadal leadtime coordinate"
    description = "Adds or normalizes CMIP6-decadal leadtime coordinate values from time and reftime."
    categories = ["metadata", "structure"]
    priority = 24
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_leadtime_fix(dataset):
            return ["leadtime coordinate should be derived/normalized from time and reftime"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_leadtime_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_leadtime_fix(dataset)