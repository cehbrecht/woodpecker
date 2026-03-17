from __future__ import annotations

import xarray as xr

from ..dataset_types import DatasetTypeDetector, register_dataset_type_detector
from ..identity import DefaultDatasetIdentityResolver, register_dataset_identity_resolver


class CMIP6DecadalDatasetTypeDetector(DatasetTypeDetector):
    dataset_type = "cmip6-decadal"
    priority = 30

    def matches(self, dataset: xr.Dataset) -> bool:
        source_name = str(dataset.attrs.get("source_name", "")).lower()
        return source_name.endswith(".nc") and "cmip6" in source_name and "decadal" in source_name


class CMIP6DecadalDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    """Scaffold resolver for CMIP6-decadal datasets.

    Keep defaults for now and extend this class as CMIP6-specific rules evolve.
    """


register_dataset_type_detector(CMIP6DecadalDatasetTypeDetector(), override=True)
register_dataset_identity_resolver(
    "cmip6-decadal", CMIP6DecadalDatasetIdentityResolver(), override=True
)
