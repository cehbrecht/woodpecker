from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity
from .cmip6 import CMIP6DatasetIdentityResolver


class CMIP6DecadalDatasetIdentityResolver(CMIP6DatasetIdentityResolver):
    """Metadata-first identity resolver for CMIP6 decadal prediction datasets.

    Inherits attr extraction and signal helpers from CMIP6DatasetIdentityResolver.
    Requires decadal-specific evidence alongside CMIP6 context.

    Decadal evidence priority (high → low):
      1. activity_id=DCPP / experiment_id startswith dcpp / sub_experiment_id s\\d{4}
      2. project_id / dataset_id containing "decadal"
      3. source_name containing both "cmip6" and "decadal" (weak)
    """

    dataset_type = "cmip6-decadal"
    priority = 30

    def _source_name_signals(self, attrs: dict[str, str]) -> list[str]:
        sn = attrs["source_name"]
        if "cmip6" in sn and "decadal" in sn:
            return ["attr:source_name contains cmip6-decadal (weak)"]
        return []

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        attrs = self._extract_attrs(dataset)
        context = self._cmip6_context_signals(attrs)
        decadal = self._decadal_signals(attrs)
        source = self._source_name_signals(attrs)

        if not ((context and decadal) or source):
            return None

        evidence = tuple(context + decadal + source)
        confidence = (0.98 if "attr:activity_id=dcpp" in evidence else 0.7) if decadal else 0.4
        dataset_id = self._resolve_dataset_id(dataset)
        project_id = self._resolve_project_id(dataset, dataset_id)

        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=confidence,
            evidence=evidence,
            metadata={"resolver": type(self).__name__, "detection_mode": "metadata-first"},
        )
