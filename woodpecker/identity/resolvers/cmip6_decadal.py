from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity
from ..common import first_str_attr, normalized_token
from ..registry import register_dataset_identity
from .fallback import DefaultDatasetIdentityResolver


@register_dataset_identity("cmip6-decadal", override=True)
class CMIP6DecadalDatasetIdentityResolver(DefaultDatasetIdentityResolver):
    """Metadata-first identity resolver for CMIP6 decadal datasets."""

    dataset_type = "cmip6-decadal"
    priority = 30

    def _metadata_signals(self, dataset: xr.Dataset) -> list[str]:
        attrs = dataset.attrs
        signals: list[str] = []

        mip_era = normalized_token(first_str_attr(attrs, ("mip_era",)))
        activity_id = normalized_token(first_str_attr(attrs, ("activity_id",)))
        experiment_id = normalized_token(first_str_attr(attrs, ("experiment_id",)))
        sub_experiment_id = normalized_token(first_str_attr(attrs, ("sub_experiment_id",)))
        project_id = normalized_token(first_str_attr(attrs, ("project_id",)))
        dataset_id = normalized_token(first_str_attr(attrs, ("dataset_id", "ds_id")))

        if mip_era == "cmip6":
            signals.append("attr:mip_era=cmip6")
        if activity_id == "dcpp":
            signals.append("attr:activity_id=dcpp")
        if experiment_id.startswith("dcpp"):
            signals.append("attr:experiment_id startswith dcpp")
        if sub_experiment_id.startswith("s"):
            signals.append("attr:sub_experiment_id startswith s")
        if "decadal" in project_id:
            signals.append("attr:project_id contains decadal")
        if "decadal" in dataset_id:
            signals.append("attr:dataset_id contains decadal")
        return signals

    def _source_name_signals(self, dataset: xr.Dataset) -> list[str]:
        source_name = normalized_token(first_str_attr(dataset.attrs, ("source_name",)))
        if "cmip6" in source_name and "decadal" in source_name:
            return ["attr:source_name contains cmip6-decadal"]
        return []

    def matches(self, dataset: xr.Dataset) -> bool:
        return bool(self._metadata_signals(dataset) or self._source_name_signals(dataset))

    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        metadata_signals = self._metadata_signals(dataset)
        source_name_signals = self._source_name_signals(dataset)
        evidence = metadata_signals + source_name_signals

        confidence = 0.7 if metadata_signals else 0.4
        if any(signal == "attr:activity_id=dcpp" for signal in metadata_signals):
            confidence = 0.98

        base = super().resolve(dataset)
        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=base.dataset_id,
            project_id=base.project_id,
            confidence=confidence,
            evidence=evidence,
            metadata={
                **base.metadata,
                "resolver": type(self).__name__,
                "detection_mode": "metadata-first",
            },
        )
