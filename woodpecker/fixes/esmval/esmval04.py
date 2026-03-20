from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry


def _lat_coord_name(dataset: xr.Dataset) -> str | None:
    for name in ("lat", "latitude"):
        if name in dataset.coords:
            return name
    return None


def _needs_lat_flip(dataset: xr.Dataset) -> bool:
    coord_name = _lat_coord_name(dataset)
    if not coord_name:
        return False
    lat = dataset[coord_name]
    if lat.ndim != 1 or lat.size < 2:
        return False
    return bool(lat.values[0] > lat.values[-1])


def _apply_lat_flip(dataset: xr.Dataset) -> bool:
    coord_name = _lat_coord_name(dataset)
    if not coord_name:
        return False

    lat = dataset[coord_name]
    if lat.ndim != 1 or lat.size < 2:
        return False

    lat_dim = lat.dims[0]
    reverse = slice(None, None, -1)
    flipped = dataset.isel({lat_dim: reverse})

    bounds_name = lat.attrs.get("bounds")
    if isinstance(bounds_name, str) and bounds_name in flipped:
        bounds = flipped[bounds_name]
        other_dims = tuple(dim for dim in bounds.dims if dim != lat_dim)
        if len(other_dims) == 1:
            flipped[bounds_name].data = bounds.isel({other_dims[0]: reverse}).data

    for name in list(dataset.data_vars):
        if lat_dim in dataset[name].dims:
            dataset[name].data = flipped[name].data
    for name in list(dataset.coords):
        if lat_dim in dataset[name].dims:
            dataset.coords[name] = flipped[name]
    return True


@FixRegistry.register
class ESMVAL04(Fix):
    code = "ESMVAL04"
    name = "Ensure latitude is increasing"
    description = "Flips datasets with decreasing latitude coordinates to increasing order."
    categories = ["structure"]
    priority = 43
    dataset = "ESMVal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_lat_flip(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_lat_flip(dataset):
            return []
        return ["latitude coordinate should be increasing"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_lat_flip(dataset):
            return False
        if dry_run:
            return True
        return _apply_lat_flip(dataset)
