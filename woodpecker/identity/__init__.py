from .base import DatasetIdentity, DatasetIdentityResolver, DatasetTypeDetector
from .common import DefaultDatasetIdentityResolver, project_id_from_dataset_id
from .registry import (
    dataset_type_matches_declared,
    identify_dataset_type,
    register_dataset_identity_resolver,
    register_dataset_type_detector,
    resolve_dataset_identity,
)

# Register built-in dataset-family detectors/resolvers.
from . import atlas  # noqa: F401, E402
from . import cmip6  # noqa: F401, E402

__all__ = [
    "DatasetIdentity",
    "DatasetIdentityResolver",
    "DatasetTypeDetector",
    "DefaultDatasetIdentityResolver",
    "project_id_from_dataset_id",
    "register_dataset_identity_resolver",
    "register_dataset_type_detector",
    "identify_dataset_type",
    "resolve_dataset_identity",
    "dataset_type_matches_declared",
]
