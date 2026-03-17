from __future__ import annotations

import xarray as xr

from .common import DefaultDatasetIdentityResolver
from .registry import register_dataset_identity


@register_dataset_identity("cmip6-decadal", override=True)
class CMIP6DecadalDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    """Scaffold resolver for CMIP6-decadal datasets."""

    dataset_type = "cmip6-decadal"
    priority = 30

    def matches(self, dataset: xr.Dataset) -> bool:
        source_name = str(dataset.attrs.get("source_name", "")).lower()
        return source_name.endswith(".nc") and "cmip6" in source_name and "decadal" in source_name
