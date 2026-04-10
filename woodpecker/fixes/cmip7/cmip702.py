from __future__ import annotations

import xarray as xr

from ..common.helpers import project_id_from_dataset
from ..registry import Fix, FixRegistry


def _needs_project_id(dataset: xr.Dataset) -> bool:
    current = dataset.attrs.get("project_id")
    if isinstance(current, str) and current.strip():
        return False
    return bool(project_id_from_dataset(dataset))


def _apply_project_id(dataset: xr.Dataset) -> bool:
    project_id = project_id_from_dataset(dataset)
    if not project_id:
        return False
    dataset.attrs["project_id"] = project_id
    return True


@FixRegistry.register
class CMIP7_0001(Fix):
    code = "CMIP7_0001"
    name = "Ensure project_id is present"
    description = "Sets project_id from dataset identifier metadata when missing."
    categories = ["metadata"]
    priority = 41
    dataset = "CMIP7"

    def matches(self, dataset: xr.Dataset) -> bool:
        return _needs_project_id(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not _needs_project_id(dataset):
            return []
        return ["project_id is missing and can be derived from dataset metadata"]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not _needs_project_id(dataset):
            return False
        if dry_run:
            return True
        return _apply_project_id(dataset)
