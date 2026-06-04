from __future__ import annotations

import xarray as xr

from woodpecker.fixes.labels import Labels
from woodpecker.fixes.registry import FixFunction, register_fix_function


def _needs_temp_to_tas_rename(dataset: xr.Dataset) -> bool:
    return "temp" in dataset.data_vars and "tas" not in dataset.data_vars


def _apply_temp_to_tas_rename(dataset: xr.Dataset) -> bool:
    if not _needs_temp_to_tas_rename(dataset):
        return False

    dataset["tas"] = dataset["temp"]
    del dataset["temp"]
    return True


@register_fix_function
class RenameTempVariableToTas(FixFunction):
    suffix = "rename_temp_variable_to_tas"
    name = "Rename temp variable to tas (plugin)"
    description = "Renames data variable temp to tas when tas is missing."
    categories = ["structure", "metadata"]
    priority = 42
    dataset = "CMIP7"
    labels = [Labels.RISK_REVERSIBLE_RENAME]

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
