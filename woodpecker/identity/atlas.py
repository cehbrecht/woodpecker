from __future__ import annotations

import xarray as xr

from .common import DefaultDatasetIdentityResolver
from .registry import register_dataset_identity


@register_dataset_identity("atlas", override=True)
class AtlasDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    dataset_type = "atlas"
    priority = 20

    def matches(self, dataset: xr.Dataset) -> bool:
        source_name = str(dataset.attrs.get("source_name", "")).lower()
        return source_name.endswith(".nc") and "atlas" in source_name

    def dataset_id(self, dataset: xr.Dataset) -> str:
        return self._first_str_attr(
            dataset, ("ds_id", "dataset_id", "id", "source_id", "source_name")
        )
