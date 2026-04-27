from __future__ import annotations

import re

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id

_SUB_EXPERIMENT_RE = re.compile(r"^s\d{4}$")


class CMIP6DatasetIdentityResolver(DatasetIdentityResolver):
    """Metadata-first identity resolver for non-decadal CMIP6 datasets.

    Detection priority (high → low):
      1. mip_era / activity_id / experiment_id / sub_experiment_id attrs
      2. project_id / dataset_id containing "cmip6"
      3. source_name containing "cmip6" (weak fallback)
    """

    dataset_type = "cmip6"
    priority = 40

    # -- attr extraction -------------------------------------------------------

    def _extract_attrs(self, dataset: xr.Dataset) -> dict[str, str]:
        """Normalize all relevant attrs once per evaluate() call."""
        raw = dataset.attrs
        return {
            "mip_era": normalized_token(first_str_attr(raw, ("mip_era",))),
            "project_id": normalized_token(first_str_attr(raw, ("project_id",))),
            "dataset_id": normalized_token(first_str_attr(raw, ("dataset_id", "ds_id"))),
            "source_name": normalized_token(first_str_attr(raw, ("source_name",))),
            "activity_id": normalized_token(first_str_attr(raw, ("activity_id",))),
            "experiment_id": normalized_token(first_str_attr(raw, ("experiment_id",))),
            "sub_experiment_id": normalized_token(first_str_attr(raw, ("sub_experiment_id",))),
        }

    def _resolve_dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("dataset_id", "ds_id", "id", "source_id", "source_name"),
        )

    def _resolve_project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit = first_str_attr(dataset.attrs, ("project_id",))
        return explicit or project_id_from_dataset_id(dataset_id)

    # -- signal helpers (accept pre-extracted attrs dict) ----------------------

    def _cmip6_context_signals(self, attrs: dict[str, str]) -> list[str]:
        signals: list[str] = []
        if attrs["mip_era"] == "cmip6":
            signals.append("attr:mip_era=cmip6")
        if "cmip6" in attrs["project_id"]:
            signals.append("attr:project_id contains cmip6")
        if "cmip6" in attrs["dataset_id"]:
            signals.append("attr:dataset_id contains cmip6")
        if "cmip6" in attrs["source_name"]:
            signals.append("attr:source_name contains cmip6")
        return signals

    def _decadal_signals(self, attrs: dict[str, str]) -> list[str]:
        signals: list[str] = []
        if attrs["activity_id"] == "dcpp":
            signals.append("attr:activity_id=dcpp")
        if attrs["experiment_id"].startswith("dcpp"):
            signals.append("attr:experiment_id startswith dcpp")
        if _SUB_EXPERIMENT_RE.match(attrs["sub_experiment_id"]):
            signals.append("attr:sub_experiment_id matches s\\d{4}")
        if "decadal" in attrs["project_id"]:
            signals.append("attr:project_id contains decadal")
        if "decadal" in attrs["dataset_id"]:
            signals.append("attr:dataset_id contains decadal")
        if "decadal" in attrs["source_name"]:
            signals.append("attr:source_name contains decadal")
        return signals

    def _source_name_signals(self, attrs: dict[str, str]) -> list[str]:
        sn = attrs["source_name"]
        if "cmip6" in sn and "decadal" not in sn:
            return ["attr:source_name contains cmip6 (weak)"]
        return []

    # -- evaluate --------------------------------------------------------------

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        """Classify the dataset as CMIP6 (non-decadal).

        Confidence tiers:
          0.95  — mip_era=CMIP6 is present
          0.60  — other CMIP6 context attrs match but mip_era is absent
          0.35  — only source_name weak signal
        Returns None if any decadal signals are detected.
        """
        attrs = self._extract_attrs(dataset)

        if self._decadal_signals(attrs):
            return None

        context = self._cmip6_context_signals(attrs)
        source = self._source_name_signals(attrs)
        evidence = tuple(context + source)

        if not evidence:
            return None

        confidence = 0.95 if "attr:mip_era=cmip6" in evidence else (0.6 if context else 0.35)
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
