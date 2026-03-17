from __future__ import annotations

import xarray as xr


def lower_source_name(dataset: xr.Dataset) -> str:
	return str(dataset.attrs.get("source_name", "")).lower()


def is_cmip6_netcdf(dataset: xr.Dataset) -> bool:
	source = lower_source_name(dataset)
	return source.endswith(".nc") and "cmip6" in source
