from __future__ import annotations

import xarray as xr

from woodpecker.identity import resolve_dataset_identity
from ..registry import Fix, FixRegistry
from .common import lower_source_name


def _needs_project_id(dataset: xr.Dataset) -> bool:
    identity = resolve_dataset_identity(dataset)
    project_id = identity.project_id
    if not project_id:
        return False
    return dataset.attrs.get("project_id") != project_id


def _apply_atlas_project_id(dataset: xr.Dataset) -> bool:
    identity = resolve_dataset_identity(dataset)
    project_id = identity.project_id
    if not project_id:
        return False
    if dataset.attrs.get("project_id") == project_id:
        return False
    dataset.attrs["project_id"] = project_id
    return True


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
        if _needs_project_id(dataset):
            return ["project_id attribute is missing or inconsistent with dataset identifier"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_project_id(dataset):
            return False
        if dry_run:
            return True
        return _apply_atlas_project_id(dataset)
