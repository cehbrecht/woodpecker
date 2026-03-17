from __future__ import annotations

import xarray as xr

from .base import DatasetIdentity, DatasetIdentityResolver, DatasetTypeDetector
from .common import DefaultDatasetIdentityResolver


_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_DETECTORS: dict[str, DatasetTypeDetector] = {}
_DEFAULT_RESOLVER = DefaultDatasetIdentityResolver()


def register_dataset_identity_resolver(
    dataset_type: str, resolver: DatasetIdentityResolver, *, override: bool = False
) -> None:
    key = dataset_type.strip().lower()
    if not key:
        raise ValueError("dataset_type must be a non-empty string")
    if key in _RESOLVERS and not override:
        raise ValueError(f"dataset identity resolver already registered for '{key}'")
    _RESOLVERS[key] = resolver


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


def resolve_dataset_identity(dataset: xr.Dataset, dataset_type: str | None = None) -> DatasetIdentity:
    effective_dataset_type = dataset_type.strip().lower() if dataset_type else identify_dataset_type(dataset)

    if effective_dataset_type:
        resolver = _RESOLVERS.get(effective_dataset_type)
        if resolver is not None:
            identity = resolver.resolve(dataset)
            return DatasetIdentity(
                dataset_id=identity.dataset_id,
                project_id=identity.project_id,
                dataset_type=effective_dataset_type,
            )

    identity = _DEFAULT_RESOLVER.resolve(dataset)
    return DatasetIdentity(
        dataset_id=identity.dataset_id,
        project_id=identity.project_id,
        dataset_type=effective_dataset_type,
    )
