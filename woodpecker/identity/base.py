from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import xarray as xr

from .utils import first_str_attr, project_id_from_dataset_id


@dataclass(frozen=True)
class DatasetIdentity:
    dataset_type: str | None
    project_id: str
    dataset_id: str
    confidence: float | None = None
    evidence: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetIdentityResolver(ABC):
    dataset_type: str = ""
    priority: int = 100

    @abstractmethod
    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        """Return identity if this resolver matches the dataset, else None."""
        ...


class DefaultDatasetIdentityResolver(DatasetIdentityResolver):
    """Generic fallback that always returns a baseline DatasetIdentity.

    This is core framework logic, not a dataset-family plugin.
    It runs only when no registered resolver matches.
    """

    dataset_type = ""
    priority = 1000

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity:
        attrs = dataset.attrs
        dataset_id = first_str_attr(attrs, ("dataset_id", "ds_id", "id", "source_id", "source_name"))
        explicit_project_id = first_str_attr(attrs, ("project_id",))
        project_id = explicit_project_id or project_id_from_dataset_id(dataset_id)
        return DatasetIdentity(
            dataset_type=None,
            dataset_id=dataset_id,
            project_id=project_id,
            confidence=0.0,
            evidence=("fallback:generic-identity",),
            metadata={"resolver": type(self).__name__, "attrs_seen": sorted(attrs.keys())},
        )
