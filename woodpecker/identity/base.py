from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import xarray as xr


@dataclass(frozen=True)
class DatasetIdentity:
    dataset_id: str
    project_id: str
    dataset_type: str | None = None


class DatasetIdentityResolver(ABC):
    @abstractmethod
    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        pass


class DatasetTypeDetector(ABC):
    dataset_type: str
    priority: int = 100

    @abstractmethod
    def matches(self, dataset: xr.Dataset) -> bool:
        pass
