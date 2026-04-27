from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id


class AtlasDatasetIdentityResolver(DatasetIdentityResolver):
    dataset_type = "atlas"
    priority = 20

    def _dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("ds_id", "dataset_id", "id", "source_id", "source_name"),
        )

    def _project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit_project_id = first_str_attr(dataset.attrs, ("project_id",))
        if explicit_project_id:
            return explicit_project_id
        return project_id_from_dataset_id(dataset_id)

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        project_id = normalized_token(first_str_attr(dataset.attrs, ("project_id",)))
        dataset_id = normalized_token(first_str_attr(dataset.attrs, ("dataset_id", "ds_id")))
        source_name = normalized_token(first_str_attr(dataset.attrs, ("source_name",)))

        if not ("atlas" in project_id or "atlas" in dataset_id or "atlas" in source_name):
            return None

        dataset_id_value = self._dataset_id(dataset)
        project_id_value = self._project_id(dataset, dataset_id_value)
        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=dataset_id_value,
            project_id=project_id_value,
            confidence=0.8,
            evidence=("attr:atlas token present",),
            metadata={"resolver": type(self).__name__},
        )