from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity
from .cmip6 import CMIP6DatasetIdentityResolver


class CMIP6DecadalDatasetIdentityResolver(CMIP6DatasetIdentityResolver):
    """Metadata-first identity resolver for CMIP6 decadal datasets."""

    dataset_type = "cmip6-decadal"
    priority = 30

    def _source_name_signals(self, dataset: xr.Dataset) -> list[str]:
        decadal_signals = self._decadal_signals(dataset)
        if any(signal == "attr:source_name contains decadal" for signal in decadal_signals):
            return ["attr:source_name contains cmip6-decadal"]
        return []

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        metadata_signals = self._cmip6_context_signals(dataset)
        decadal_signals = self._decadal_signals(dataset)
        source_name_signals = self._source_name_signals(dataset)

        if not ((metadata_signals and decadal_signals) or source_name_signals):
            return None

        evidence = tuple(metadata_signals + decadal_signals + source_name_signals)

        confidence = 0.7 if decadal_signals else 0.4
        if any(signal == "attr:activity_id=dcpp" for signal in decadal_signals):
            confidence = 0.98

        dataset_id = self._dataset_id(dataset)
        project_id = self._project_id(dataset, dataset_id)

        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=confidence,
            evidence=evidence,
            metadata={
                "resolver": type(self).__name__,
                "detection_mode": "metadata-first",
            },
        )
