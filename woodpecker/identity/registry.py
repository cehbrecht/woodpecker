from __future__ import annotations

from typing import TypeVar

import xarray as xr

from .base import DatasetIdentity, DatasetIdentityResolver
from .resolvers.fallback import DefaultDatasetIdentityResolver

_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_DEFAULT_RESOLVER = DefaultDatasetIdentityResolver()
_ResolverClass = TypeVar("_ResolverClass", bound=type[DatasetIdentityResolver])


def _register_dataset_identity_resolver(
    dataset_type: str, resolver: DatasetIdentityResolver, *, override: bool = False
) -> None:
    key = dataset_type.strip().lower()
    if not key:
        raise ValueError("dataset_type must be a non-empty string")
    if key in _RESOLVERS and not override:
        raise ValueError(f"dataset identity resolver already registered for '{key}'")
    resolver.dataset_type = key
    _RESOLVERS[key] = resolver


def register_dataset_identity(dataset_type: str, *, override: bool = False) -> callable:
    """Decorator to register a dataset identity resolver class.

    The resolver class must be instantiable without required constructor args.
    """

    def _decorator(resolver_cls: _ResolverClass) -> _ResolverClass:
        _register_dataset_identity_resolver(dataset_type, resolver_cls(), override=override)
        return resolver_cls

    return _decorator


def _identify_dataset_type(dataset: xr.Dataset) -> str | None:
    identity = _resolve_with_registry(dataset)
    if identity is not None:
        return identity.dataset_type
    return None


def _resolver_score(resolver: DatasetIdentityResolver, identity: DatasetIdentity) -> tuple[float, int]:
    confidence = identity.confidence if identity.confidence is not None else 1.0
    priority = int(getattr(resolver, "priority", 100))
    return confidence, -priority


def _resolve_with_registry(dataset: xr.Dataset) -> DatasetIdentity | None:
    resolvers = sorted(_RESOLVERS.values(), key=lambda r: int(getattr(r, "priority", 100)))
    candidates: list[tuple[DatasetIdentityResolver, DatasetIdentity]] = []

    for resolver in resolvers:
        identity = resolver.evaluate(dataset)
        if identity is None:
            continue
        normalized_dataset_type = resolver.dataset_type.strip().lower() or identity.dataset_type
        candidate = DatasetIdentity(
            dataset_type=normalized_dataset_type.strip().lower() if normalized_dataset_type else None,
            dataset_id=identity.dataset_id,
            project_id=identity.project_id,
            confidence=identity.confidence,
            evidence=list(identity.evidence),
            metadata=dict(identity.metadata),
        )
        candidates.append((resolver, candidate))

    if not candidates:
        return None

    _, best_identity = max(candidates, key=lambda item: _resolver_score(item[0], item[1]))
    return best_identity


def dataset_type_matches_declared(
    fix_dataset: str | None, detected_dataset_type: str | None
) -> bool:
    if not fix_dataset or not detected_dataset_type:
        return True
    return fix_dataset.strip().lower() == detected_dataset_type.strip().lower()


def resolve_dataset_identity(dataset: xr.Dataset) -> DatasetIdentity:
    identity = _resolve_with_registry(dataset)
    if identity is not None:
        return identity
    return _DEFAULT_RESOLVER.resolve(dataset)
