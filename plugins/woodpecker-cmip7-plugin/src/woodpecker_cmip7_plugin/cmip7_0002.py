from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, register_fix


def _needs_temp_to_tas_rename(dataset: xr.Dataset) -> bool:
    return "temp" in dataset.data_vars and "tas" not in dataset.data_vars


def _apply_temp_to_tas_rename(dataset: xr.Dataset) -> bool:
    if not _needs_temp_to_tas_rename(dataset):
        return False

    dataset["tas"] = dataset["temp"]
    del dataset["temp"]
    return True


@register_fix
class RenameTempVariableToTasFix(Fix):
    local_id = "0002"
    name = "Rename temp variable to tas (plugin)"
    description = "Renames data variable temp to tas when tas is missing."
    categories = ["structure", "metadata"]
    priority = 42
    dataset = "CMIP7"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_temp_to_tas_rename(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_temp_to_tas_rename(dataset):
            return []
        return ["temp should be renamed to tas"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_temp_to_tas_rename(dataset):
            return False
        if dry_run:
            return True
        return _apply_temp_to_tas_rename(dataset)
