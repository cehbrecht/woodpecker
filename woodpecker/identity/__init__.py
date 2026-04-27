from .base import DatasetIdentity, DatasetIdentityResolver
from .registry import (
    dataset_type_matches_declared,
    register_dataset_identity,
    resolve_dataset_identity,
)

# --- register built-in dataset-family resolvers ---
from .resolvers.atlas import AtlasDatasetIdentityResolver
from .resolvers.cmip6 import CMIP6DatasetIdentityResolver
from .resolvers.cmip6_decadal import CMIP6DecadalDatasetIdentityResolver

register_dataset_identity("atlas", override=True)(AtlasDatasetIdentityResolver)
register_dataset_identity("cmip6", override=True)(CMIP6DatasetIdentityResolver)
register_dataset_identity("cmip6-decadal", override=True)(CMIP6DecadalDatasetIdentityResolver)

del AtlasDatasetIdentityResolver, CMIP6DatasetIdentityResolver, CMIP6DecadalDatasetIdentityResolver

__all__ = [
    "DatasetIdentity",
    "DatasetIdentityResolver",
    "register_dataset_identity",
    "resolve_dataset_identity",
    "dataset_type_matches_declared",
]
