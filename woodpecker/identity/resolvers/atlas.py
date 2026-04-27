from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id


class AtlasDatasetIdentityResolver(DatasetIdentityResolver):
    dataset_type = "atlas"
    priority = 20

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        attrs = dataset.attrs
        project_id_raw = normalized_token(first_str_attr(attrs, ("project_id",)))
        dataset_id_raw = normalized_token(first_str_attr(attrs, ("dataset_id", "ds_id")))
        source_name_raw = normalized_token(first_str_attr(attrs, ("source_name",)))

        if not ("atlas" in project_id_raw or "atlas" in dataset_id_raw or "atlas" in source_name_raw):
            return None

        dataset_id = first_str_attr(attrs, ("ds_id", "dataset_id", "id", "source_id", "source_name"))
        explicit_project_id = first_str_attr(attrs, ("project_id",))
        project_id = explicit_project_id or project_id_from_dataset_id(dataset_id)

        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=0.8,
            evidence=("attr:atlas token present",),
            metadata={"resolver": type(self).__name__},
        )