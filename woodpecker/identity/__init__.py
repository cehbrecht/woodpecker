from .base import DatasetIdentity, DatasetIdentityResolver
from .common import DefaultDatasetIdentityResolver, project_id_from_dataset_id
from .registry import (
    dataset_type_matches_declared,
    identify_dataset_type,
    register_dataset_identity_resolver,
    resolve_dataset_identity,
)

# Register built-in dataset-family detectors/resolvers.
from . import atlas  # noqa: F401, E402
from . import cmip6  # noqa: F401, E402

__all__ = [
    "DatasetIdentity",
    "DatasetIdentityResolver",
    "DefaultDatasetIdentityResolver",
    "project_id_from_dataset_id",
    "register_dataset_identity_resolver",
    "identify_dataset_type",
    "resolve_dataset_identity",
    "dataset_type_matches_declared",
]
