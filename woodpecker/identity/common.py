from __future__ import annotations

import xarray as xr

from .base import DatasetIdentity, DatasetIdentityResolver


def project_id_from_dataset_id(dataset_id: str) -> str:
    if not dataset_id:
        return ""
    return dataset_id.split(".", 1)[0]


class DefaultDatasetIdentityResolver(DatasetIdentityResolver):
    def _first_str_attr(self, dataset: xr.Dataset, keys: tuple[str, ...]) -> str:
        for key in keys:
            value = dataset.attrs.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def dataset_id(self, dataset: xr.Dataset) -> str:
        return self._first_str_attr(
            dataset, ("dataset_id", "ds_id", "id", "source_id", "source_name")
        )

    def project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit_project_id = self._first_str_attr(dataset, ("project_id",))
        if explicit_project_id:
            return explicit_project_id
        return project_id_from_dataset_id(dataset_id)

    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        dataset_id = self.dataset_id(dataset)
        project_id = self.project_id(dataset, dataset_id)
        return DatasetIdentity(dataset_id=dataset_id, project_id=project_id, dataset_type=None)
