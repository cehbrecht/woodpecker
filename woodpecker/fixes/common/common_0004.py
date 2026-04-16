from __future__ import annotations

from typing import Any

import xarray as xr

from ..registry import Fix, FixRegistry
from .constants import COMMON_PREFIX


def _merge_dims_from_config(config: dict[str, Any]) -> tuple[str, ...]:
    raw = config.get("dims", ())
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, (list, tuple)):
        values = list(raw)
    else:
        return ()

    out: list[str] = []
    for value in values:
        name = str(value).strip()
        if name and name not in out:
            out.append(name)
    return tuple(out)


def _can_merge_dims(dataset: xr.Dataset, dims: tuple[str, ...]) -> bool:
    if len(dims) < 2:
        return False
    if any(dim not in dataset.sizes for dim in dims):
        return False

    sizes = [dataset.sizes[dim] for dim in dims]
    if any(size != sizes[0] for size in sizes):
        return False

    for dim in dims[1:]:
        for name in dataset.data_vars:
            if dim in dataset[name].dims:
                return True
        for name in dataset.coords:
            if dim in dataset[name].dims:
                return True
    return False


def _apply_merge_dims(dataset: xr.Dataset, dims: tuple[str, ...]) -> bool:
    if not _can_merge_dims(dataset, dims):
        return False

    target_dim = dims[0]
    changed = False
    for dim in dims[1:]:
        for name in list(dataset.data_vars):
            if dim in dataset[name].dims:
                dataset[name] = dataset[name].rename({dim: target_dim})
                changed = True
        for name in list(dataset.coords):
            if dim in dataset[name].dims:
                dataset.coords[name] = dataset[name].rename({dim: target_dim})
                changed = True

    return changed


@FixRegistry.register
class COMMON_0004(Fix):
    code = f"{COMMON_PREFIX}0004"
    name = "Merge equivalent dimensions"
    description = "Merges two or more same-sized dimensions into the first configured dimension."
    categories = ["structure"]
    priority = 32
    dataset = None

    def _dims(self) -> tuple[str, ...]:
        config = getattr(self, "config", {}) or {}
        return _merge_dims_from_config(config)

    def matches(self, dataset: xr.Dataset) -> bool:
        return _can_merge_dims(dataset, self._dims())

    def check(self, dataset: xr.Dataset) -> list[str]:
        dims = self._dims()
        if not _can_merge_dims(dataset, dims):
            return []
        return [f"dimensions can be merged: {', '.join(dims)}"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        dims = self._dims()
        if not _can_merge_dims(dataset, dims):
            return False
        if dry_run:
            return True
        return _apply_merge_dims(dataset, dims)
