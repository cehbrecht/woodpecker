from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity
from ..common import first_str_attr, normalized_token
from ..registry import register_dataset_identity
from .fallback import DefaultDatasetIdentityResolver


@register_dataset_identity("atlas", override=True)
class AtlasDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    dataset_type = "atlas"
    priority = 20

    def matches(self, dataset: xr.Dataset) -> bool:
        project_id = normalized_token(first_str_attr(dataset.attrs, ("project_id",)))
        dataset_id = normalized_token(first_str_attr(dataset.attrs, ("dataset_id", "ds_id")))
        source_name = normalized_token(first_str_attr(dataset.attrs, ("source_name",)))

        return "atlas" in project_id or "atlas" in dataset_id or "atlas" in source_name

    def dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("ds_id", "dataset_id", "id", "source_id", "source_name"),
        )

    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        base = super().resolve(dataset)
        evidence = ["attr:atlas token present"]
        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=self.dataset_id(dataset),
            project_id=base.project_id,
            confidence=0.8,
            evidence=evidence,
            metadata={**base.metadata, "resolver": type(self).__name__},
        )