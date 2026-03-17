from __future__ import annotations

import xarray as xr


def lower_source_name(dataset: xr.Dataset) -> str:
    return str(dataset.attrs.get("source_name", "")).lower()
