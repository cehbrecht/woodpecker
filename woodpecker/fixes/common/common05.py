from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .helpers import remove_encoding_key, vars_with_encoding_key

_COORDS = ("time", "lat", "latitude", "lon", "longitude")


def _needs_coord_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    candidates = [name for name in _COORDS if name in dataset.coords]
    return bool(vars_with_encoding_key(dataset, candidates, "_FillValue"))


def _apply_coord_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    candidates = [name for name in _COORDS if name in dataset.coords]
    vars_to_fix = vars_with_encoding_key(dataset, candidates, "_FillValue")
    return remove_encoding_key(dataset, vars_to_fix, "_FillValue")


@FixRegistry.register
class COMMON05(Fix):
    code = "COMMON_0003"
    name = "Remove coordinate FillValue encodings"
    description = "Removes _FillValue encoding entries from common coordinate variables."
    categories = ["metadata", "structure"]
    priority = 34
    dataset = None

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
