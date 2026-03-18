from __future__ import annotations

import xarray as xr


EXPECTED_LEADTIME_ATTRS = {
    "units": "days",
    "long_name": "Time elapsed since the start of the forecast",
    "standard_name": "forecast_period",
}


def leadtime_metadata_invalid(leadtime: xr.DataArray) -> bool:
    return any(leadtime.attrs.get(key) != value for key, value in EXPECTED_LEADTIME_ATTRS.items())


def apply_leadtime_metadata(leadtime: xr.DataArray) -> None:
    for key, value in EXPECTED_LEADTIME_ATTRS.items():
        leadtime.attrs[key] = value