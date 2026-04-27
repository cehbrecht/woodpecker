from __future__ import annotations

import re

import xarray as xr

from ..base import DatasetIdentity, DatasetIdentityResolver
from ..utils import first_str_attr, normalized_token, project_id_from_dataset_id


class CMIP6DatasetIdentityResolver(DatasetIdentityResolver):
    """Metadata-first identity resolver for non-decadal CMIP6 datasets."""

    dataset_type = "cmip6"
    priority = 40

    def _cmip6_context_signals(self, dataset: xr.Dataset) -> list[str]:
        attrs = dataset.attrs
        signals: list[str] = []

        mip_era = normalized_token(first_str_attr(attrs, ("mip_era",)))
        project_id = normalized_token(first_str_attr(attrs, ("project_id",)))
        dataset_id = normalized_token(first_str_attr(attrs, ("dataset_id", "ds_id")))
        source_name = normalized_token(first_str_attr(attrs, ("source_name",)))

        if mip_era == "cmip6":
            signals.append("attr:mip_era=cmip6")
        if "cmip6" in project_id:
            signals.append("attr:project_id contains cmip6")
        if "cmip6" in dataset_id:
            signals.append("attr:dataset_id contains cmip6")
        if "cmip6" in source_name:
            signals.append("attr:source_name contains cmip6")
        return signals

    def _decadal_signals(self, dataset: xr.Dataset) -> list[str]:
        attrs = dataset.attrs
        decadal: list[str] = []

        activity_id = normalized_token(first_str_attr(attrs, ("activity_id",)))
        experiment_id = normalized_token(first_str_attr(attrs, ("experiment_id",)))
        sub_experiment_id = normalized_token(first_str_attr(attrs, ("sub_experiment_id",)))
        project_id = normalized_token(first_str_attr(attrs, ("project_id",)))
        dataset_id = normalized_token(first_str_attr(attrs, ("dataset_id", "ds_id")))
        source_name = normalized_token(first_str_attr(attrs, ("source_name",)))

        if activity_id == "dcpp":
            decadal.append("attr:activity_id=dcpp")
        if experiment_id.startswith("dcpp"):
            decadal.append("attr:experiment_id startswith dcpp")
        if re.match(r"^s\d{4}$", sub_experiment_id):
            decadal.append("attr:sub_experiment_id startswith s")
        if "decadal" in project_id:
            decadal.append("attr:project_id contains decadal")
        if "decadal" in dataset_id:
            decadal.append("attr:dataset_id contains decadal")
        if "decadal" in source_name:
            decadal.append("attr:source_name contains decadal")
        return decadal

    def _source_name_signals(self, dataset: xr.Dataset) -> list[str]:
        source_name = normalized_token(first_str_attr(dataset.attrs, ("source_name",)))
        if "cmip6" in source_name and "decadal" not in source_name:
            return ["attr:source_name contains cmip6 (weak)"]
        return []

    def _dataset_id(self, dataset: xr.Dataset) -> str:
        return first_str_attr(
            dataset.attrs,
            ("dataset_id", "ds_id", "id", "source_id", "source_name"),
        )

    def _project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit_project_id = first_str_attr(dataset.attrs, ("project_id",))
        if explicit_project_id:
            return explicit_project_id
        return project_id_from_dataset_id(dataset_id)

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        if self._decadal_signals(dataset):
            return None

        metadata_signals = self._cmip6_context_signals(dataset)
        source_name_signals = self._source_name_signals(dataset)
        evidence = tuple(metadata_signals + source_name_signals)

        if not evidence:
            return None

        confidence = 0.6 if metadata_signals else 0.35
        if any(signal == "attr:mip_era=cmip6" for signal in metadata_signals):
            confidence = 0.95

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
