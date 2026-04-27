from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity
from ..registry import register_dataset_identity
from .cmip6 import CMIP6DatasetIdentityResolver


@register_dataset_identity("cmip6-decadal", override=True)
class CMIP6DecadalDatasetIdentityResolver(CMIP6DatasetIdentityResolver):
    """Metadata-first identity resolver for CMIP6 decadal datasets."""

    dataset_type = "cmip6-decadal"
    priority = 30

    def _source_name_signals(self, dataset: xr.Dataset) -> list[str]:
        decadal_signals = self._decadal_signals(dataset)
        if any(signal == "attr:source_name contains decadal" for signal in decadal_signals):
            return ["attr:source_name contains cmip6-decadal"]
        return []

    def matches(self, dataset: xr.Dataset) -> bool:
        metadata_signals = self._cmip6_context_signals(dataset)
        decadal_signals = self._decadal_signals(dataset)
        source_name_signals = self._source_name_signals(dataset)

        return bool((metadata_signals and decadal_signals) or source_name_signals)

    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        metadata_signals = self._cmip6_context_signals(dataset)
        decadal_signals = self._decadal_signals(dataset)
        source_name_signals = self._source_name_signals(dataset)
        evidence = metadata_signals + decadal_signals + source_name_signals

        confidence = 0.7 if decadal_signals else 0.4
        if any(signal == "attr:activity_id=dcpp" for signal in decadal_signals):
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
