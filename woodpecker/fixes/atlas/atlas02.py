from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry
from .common import apply_atlas_project_id, lower_source_name, needs_project_id


@FixRegistry.register
class ATLAS02(Fix):
    code = "ATLAS02"
    name = "ATLAS project_id normalization"
    description = "Adds or normalizes ATLAS project_id from dataset identifier prefix."
    categories = ["metadata"]
    priority = 21
    dataset = "ATLAS"

    def matches(self, dataset: xr.Dataset) -> bool:
        source = lower_source_name(dataset)
        return source.endswith(".nc") and "atlas" in source

    def check(self, dataset: xr.Dataset) -> list[str]:
        if needs_project_id(dataset):
            return ["project_id attribute is missing or inconsistent with dataset identifier"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not needs_project_id(dataset):
            return False
        if dry_run:
            return True
        return apply_atlas_project_id(dataset)
