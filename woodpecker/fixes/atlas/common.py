from __future__ import annotations

import xarray as xr

from ..identity import DefaultDatasetIdentityResolver, register_dataset_identity_resolver


def lower_source_name(dataset: xr.Dataset) -> str:
    return str(dataset.attrs.get("source_name", "")).lower()


class AtlasDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    def dataset_id(self, dataset: xr.Dataset) -> str:
        return self._first_str_attr(dataset, ("ds_id", "dataset_id", "id", "source_id", "source_name"))


register_dataset_identity_resolver("atlas", AtlasDatasetIdentityResolver(), override=True)
