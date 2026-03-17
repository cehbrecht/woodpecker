from __future__ import annotations

from abc import ABC, abstractmethod

import xarray as xr


class DatasetTypeDetector(ABC):
    dataset_type: str
    priority: int = 100

    @abstractmethod
    def matches(self, dataset: xr.Dataset) -> bool:
        pass


_DETECTORS: dict[str, DatasetTypeDetector] = {}


def register_dataset_type_detector(
    detector: DatasetTypeDetector, *, override: bool = False
) -> None:
    dataset_type = getattr(detector, "dataset_type", "").strip().lower()
    if not dataset_type:
        raise ValueError("dataset type detector must define a non-empty dataset_type")
    if dataset_type in _DETECTORS and not override:
        raise ValueError(f"dataset type detector already registered for '{dataset_type}'")
    _DETECTORS[dataset_type] = detector


def identify_dataset_type(dataset: xr.Dataset) -> str | None:
    detectors = sorted(_DETECTORS.values(), key=lambda d: getattr(d, "priority", 100))
    for detector in detectors:
        if detector.matches(dataset):
            return detector.dataset_type.strip().lower()
    return None


def dataset_type_matches_declared(fix_dataset: str | None, detected_dataset_type: str | None) -> bool:
    if not fix_dataset or not detected_dataset_type:
        return True
    return fix_dataset.strip().lower() == detected_dataset_type.strip().lower()
