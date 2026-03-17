from __future__ import annotations

import xarray as xr

from .common import DefaultDatasetIdentityResolver
from .registry import register_dataset_identity


@register_dataset_identity("cmip6", override=True)
class CMIP6DatasetIdentityResolver(DefaultDatasetIdentityResolver):
    """Identity resolver for non-decadal CMIP6 datasets."""

    dataset_type = "cmip6"
    priority = 40

    def matches(self, dataset: xr.Dataset) -> bool:
        source_name = str(dataset.attrs.get("source_name", "")).lower()
        return source_name.endswith(".nc") and "cmip6" in source_name and "decadal" not in source_name
