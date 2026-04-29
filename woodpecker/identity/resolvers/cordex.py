from __future__ import annotations

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id


class CordexDatasetIdentityResolver(DatasetIdentityResolver):
    """Metadata-first identity resolver for CORDEX datasets."""

    dataset_type = "cordex"
    priority = 35

    def _extract_attrs(self, dataset: xr.Dataset) -> dict[str, str]:
        raw = dataset.attrs
        return {
            "project_id": normalized_token(first_str_attr(raw, ("project_id",))),
            "dataset_id": normalized_token(first_str_attr(raw, ("dataset_id", "ds_id"))),
            "source_name": normalized_token(first_str_attr(raw, ("source_name",))),
            "activity_id": normalized_token(first_str_attr(raw, ("activity_id",))),
            "domain_id": normalized_token(first_str_attr(raw, ("domain_id",))),
            "rcm_model_id": normalized_token(first_str_attr(raw, ("rcm_model_id",))),
        }

    def _resolve_dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("dataset_id", "ds_id", "id", "source_id", "source_name"),
        )

    def _resolve_project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit = first_str_attr(dataset.attrs, ("project_id",))
        return explicit or project_id_from_dataset_id(dataset_id)

    def _signals(self, attrs: dict[str, str]) -> list[str]:
        signals: list[str] = []
        if attrs["project_id"] == "cordex":
            signals.append("attr:project_id=cordex")
        if attrs["activity_id"] == "cordex":
            signals.append("attr:activity_id=cordex")
        if attrs["domain_id"] and attrs["rcm_model_id"]:
            signals.append("attrs:domain_id+rcm_model_id")
        if "cordex" in attrs["dataset_id"]:
            signals.append("attr:dataset_id contains cordex")
        if "cordex" in attrs["source_name"]:
            signals.append("attr:source_name contains cordex")
        return signals

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        attrs = self._extract_attrs(dataset)
        evidence = tuple(self._signals(attrs))

        if not evidence:
            return None

        confidence = 0.95 if "attr:project_id=cordex" in evidence else 0.65
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
