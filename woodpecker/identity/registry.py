from __future__ import annotations

import xarray as xr
from typing import TypeVar

from .base import DatasetIdentity, DatasetIdentityResolver
from .common import DefaultDatasetIdentityResolver


_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_DEFAULT_RESOLVER = DefaultDatasetIdentityResolver()
_ResolverClass = TypeVar("_ResolverClass", bound=type[DatasetIdentityResolver])


def register_dataset_identity_resolver(
    dataset_type: str, resolver: DatasetIdentityResolver, *, override: bool = False
) -> None:
    key = dataset_type.strip().lower()
    if not key:
        raise ValueError("dataset_type must be a non-empty string")
    if key in _RESOLVERS and not override:
        raise ValueError(f"dataset identity resolver already registered for '{key}'")
    resolver.dataset_type = key
    _RESOLVERS[key] = resolver


def register_dataset_identity(
    dataset_type: str, *, override: bool = False
) -> callable:
    """Decorator to register a dataset identity resolver class.

    The resolver class must be instantiable without required constructor args.
    """

    def _decorator(resolver_cls: _ResolverClass) -> _ResolverClass:
        register_dataset_identity_resolver(dataset_type, resolver_cls(), override=override)
        return resolver_cls

    return _decorator


def identify_dataset_type(dataset: xr.Dataset) -> str | None:
    resolvers = sorted(_RESOLVERS.values(), key=lambda r: getattr(r, "priority", 100))
    for resolver in resolvers:
        if resolver.matches(dataset):
            return resolver.dataset_type.strip().lower()
    return None


def dataset_type_matches_declared(fix_dataset: str | None, detected_dataset_type: str | None) -> bool:
    if not fix_dataset or not detected_dataset_type:
        return True
    return fix_dataset.strip().lower() == detected_dataset_type.strip().lower()


def resolve_dataset_identity(dataset: xr.Dataset) -> DatasetIdentity:
    effective_dataset_type = identify_dataset_type(dataset)

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
