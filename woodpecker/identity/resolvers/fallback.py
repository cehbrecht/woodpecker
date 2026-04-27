from __future__ import annotations

from typing import Any

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, project_id_from_dataset_id


class FallbackDatasetIdentityResolver(DatasetIdentityResolver):
    """Fallback resolver that always derives a generic identity."""

    dataset_type = ""
    priority = 1000

    def _dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("dataset_id", "ds_id", "id", "source_id", "source_name"),
        )

    def _project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit_project_id = first_str_attr(dataset.attrs, ("project_id",))
        if explicit_project_id:
            return explicit_project_id
        return project_id_from_dataset_id(dataset_id)

    def _metadata(self, dataset: xr.Dataset) -> dict[str, Any]:
        return {"resolver": type(self).__name__, "attrs_seen": sorted(dataset.attrs.keys())}

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        dataset_id = self._dataset_id(dataset)
        project_id = self._project_id(dataset, dataset_id)
        return DatasetIdentity(
            dataset_type=None,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=0.0,
            evidence=("fallback:generic-identity",),
            metadata=self._metadata(dataset),
        )
