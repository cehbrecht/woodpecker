from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id


class AtlasDatasetIdentityResolver(DatasetIdentityResolver):
    """Metadata-first identity resolver for Atlas datasets.

    Detection priority (high → low):
      1. project_id containing "atlas"
      2. dataset_id / ds_id containing "atlas"
      3. source_name containing "atlas" (weak fallback)
    """

    dataset_type = "atlas"
    priority = 20

    # -- attr extraction -------------------------------------------------------

    def _extract_attrs(self, dataset: xr.Dataset) -> dict[str, str]:
        """Normalize all relevant attrs once per evaluate() call."""
        raw = dataset.attrs
        return {
            "project_id": normalized_token(first_str_attr(raw, ("project_id",))),
            "dataset_id": normalized_token(first_str_attr(raw, ("dataset_id", "ds_id"))),
            "source_name": normalized_token(first_str_attr(raw, ("source_name",))),
        }

    def _resolve_dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("ds_id", "dataset_id", "id", "source_id", "source_name"),
        )

    def _resolve_project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit = first_str_attr(dataset.attrs, ("project_id",))
        return explicit or project_id_from_dataset_id(dataset_id)

    # -- signal helpers --------------------------------------------------------

    def _signals(self, attrs: dict[str, str]) -> list[str]:
        signals: list[str] = []
        if "atlas" in attrs["project_id"]:
            signals.append("attr:project_id contains atlas")
        if "atlas" in attrs["dataset_id"]:
            signals.append("attr:dataset_id contains atlas")
        if "atlas" in attrs["source_name"]:
            signals.append("attr:source_name contains atlas")
        return signals

    # -- evaluate --------------------------------------------------------------

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        """Classify the dataset as Atlas.

        Confidence tiers:
          0.90  — project_id contains "atlas"
          0.70  — dataset_id contains "atlas" (no project_id match)
          0.50  — source_name only (weak)
        Returns None if no Atlas signals are detected.
        """
        attrs = self._extract_attrs(dataset)
        evidence = tuple(self._signals(attrs))

        if not evidence:
            return None

        if "attr:project_id contains atlas" in evidence:
            confidence = 0.90
        elif "attr:dataset_id contains atlas" in evidence:
            confidence = 0.70
        else:
            confidence = 0.50

        dataset_id = self._resolve_dataset_id(dataset)
        project_id = self._resolve_project_id(dataset, dataset_id)

        return DatasetIdentity(
            dataset_type=self.dataset_type,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=confidence,
            evidence=evidence,
            metadata={"resolver": type(self).__name__},
        )