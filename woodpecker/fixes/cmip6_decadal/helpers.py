from __future__ import annotations

import re

import xarray as xr

from ..common.helpers import lower_source_name

_START_YEAR_PATTERN = re.compile(r"s(\d{4})(?:[^\d]|$)")
_METADATA_SOURCES = (
    "sub_experiment_id",
    "startdate",
    "source_name",
    "further_info_url",
)

EXPECTED_LEADTIME_ATTRS = {
    "units": "days",
    "long_name": "Time elapsed since the start of the forecast",
    "standard_name": "forecast_period",
}


def is_cmip6_netcdf(dataset: xr.Dataset) -> bool:
    """Return True for source names that look like CMIP6 NetCDF files."""
    source = lower_source_name(dataset)
    return source.endswith(".nc") and "cmip6" in source


def is_cmip6_decadal_netcdf(dataset: xr.Dataset) -> bool:
    """Return True for source names that look like CMIP6-decadal NetCDF files."""
    source = lower_source_name(dataset)
    return source.endswith(".nc") and "cmip6" in source and "decadal" in source


def extract_start_year(dataset: xr.Dataset) -> int | None:
    """Return the hindcast start year from the first matching sYYYY token."""
    for key in _METADATA_SOURCES:
        source = dataset.attrs.get(key)
        if not isinstance(source, str) or not source:
            continue
        match = _START_YEAR_PATTERN.search(source)
        if match:
            return int(match.group(1))
    return None


def normalized_start_token(dataset: xr.Dataset) -> str | None:
    """Return canonical sYYYY11 start token for a dataset, or None."""
    year = extract_start_year(dataset)
    if year is None:
        return None
    return f"s{year:04d}11"


def leadtime_metadata_invalid(leadtime: xr.DataArray) -> bool:
    """Return True when leadtime metadata does not match expected CMIP6-decadal values."""
    return any(leadtime.attrs.get(key) != value for key, value in EXPECTED_LEADTIME_ATTRS.items())


def apply_leadtime_metadata(leadtime: xr.DataArray) -> None:
    """Apply expected leadtime metadata attributes in place."""
    for key, value in EXPECTED_LEADTIME_ATTRS.items():
        leadtime.attrs[key] = value
