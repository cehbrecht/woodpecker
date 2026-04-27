from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import xarray as xr


@dataclass(frozen=True)
class DatasetIdentity:
    dataset_type: str | None
    project_id: str
    dataset_id: str
    confidence: float | None = None
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetIdentityResolver(ABC):
    dataset_type: str = ""
    priority: int = 100

    @abstractmethod
    def matches(self, dataset: xr.Dataset) -> bool:
        pass

    @abstractmethod
    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        pass

    def evaluate(self, dataset: xr.Dataset) -> DatasetIdentity | None:
        if not self.matches(dataset):
            return None
        return self.resolve(dataset)
