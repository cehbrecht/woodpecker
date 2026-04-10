from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry

_COORDS = ("time", "lat", "latitude", "lon", "longitude")


def _needs_coord_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    for name in _COORDS:
        if name in dataset.coords and "_FillValue" in dataset[name].encoding:
            return True
    return False


def _apply_coord_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    changed = False
    for name in _COORDS:
        if name not in dataset.coords:
            continue
        encoding = dataset[name].encoding
        if "_FillValue" in encoding:
            encoding.pop("_FillValue", None)
            changed = True
    return changed


@FixRegistry.register
class CMIP705(Fix):
    code = "CMIP705"
    name = "Remove coordinate FillValue encodings"
    description = "Removes _FillValue encoding entries from common coordinate variables."
    categories = ["metadata", "structure"]
    priority = 44
    dataset = "CMIP7"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_coord_fillvalue_cleanup(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_coord_fillvalue_cleanup(dataset):
            return []
        return ["coordinate encodings should not define _FillValue"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_coord_fillvalue_cleanup(dataset):
            return False
        if dry_run:
            return True
        return _apply_coord_fillvalue_cleanup(dataset)
