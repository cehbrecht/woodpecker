from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, register_fix

from .helpers import project_id_from_dataset


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


@register_fix
class EnsureProjectIdIsPresentFix(Fix):
    local_id = "ensure_project_id_present"
    name = "Ensure project_id is present (plugin)"
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
