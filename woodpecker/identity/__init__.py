# Register built-in dataset-family detectors/resolvers.
from .base import DatasetIdentity, DatasetIdentityResolver
from .resolvers.atlas import AtlasDatasetIdentityResolver
from .resolvers.cmip6 import CMIP6DatasetIdentityResolver
from .resolvers.cmip6_decadal import CMIP6DecadalDatasetIdentityResolver
from .utils import first_str_attr, normalized_token, project_id_from_dataset_id
from .registry import (
    dataset_type_matches_declared,
    register_dataset_identity,
    register_dataset_identity_resolver,
    resolve_dataset_identity,
)

# Register built-ins in one place.
register_dataset_identity_resolver("atlas", AtlasDatasetIdentityResolver, override=True)
register_dataset_identity_resolver("cmip6", CMIP6DatasetIdentityResolver, override=True)
register_dataset_identity_resolver("cmip6-decadal", CMIP6DecadalDatasetIdentityResolver, override=True)

__all__ = [
    "DatasetIdentity",
    "DatasetIdentityResolver",
    "first_str_attr",
    "normalized_token",
    "project_id_from_dataset_id",
    "register_dataset_identity",
    "register_dataset_identity_resolver",
    "resolve_dataset_identity",
    "dataset_type_matches_declared",
]
