# Register built-in dataset-family detectors/resolvers.
from .resolvers import atlas as _atlas  # noqa: F401, E402
from .resolvers import cmip6 as _cmip6  # noqa: F401, E402
from .resolvers import cmip6_decadal as _cmip6_decadal  # noqa: F401, E402
from .base import DatasetIdentity, DatasetIdentityResolver
from .registry import (
    dataset_type_matches_declared,
    register_dataset_identity,
    resolve_dataset_identity,
)

__all__ = [
    "DatasetIdentity",
    "DatasetIdentityResolver",
    "register_dataset_identity",
    "resolve_dataset_identity",
    "dataset_type_matches_declared",
]
