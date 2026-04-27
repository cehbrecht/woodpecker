from __future__ import annotations

from typing import Callable, TypeVar

import xarray as xr

from .base import DatasetIdentity, DatasetIdentityResolver
from .resolvers.fallback import FallbackDatasetIdentityResolver

_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_FALLBACK_RESOLVER = FallbackDatasetIdentityResolver()
_ResolverClass = TypeVar("_ResolverClass", bound=type[DatasetIdentityResolver])
_DEFAULT_PRIORITY = 100
_DEFAULT_CONFIDENCE = 1.0


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


def register_dataset_identity_resolver(
    dataset_type: str,
    resolver_cls: type[DatasetIdentityResolver],
    *,
    override: bool = False,
) -> None:
    """Register a resolver class for a dataset type."""

    _register_dataset_identity_resolver(dataset_type, resolver_cls(), override=override)


def register_dataset_identity(
    dataset_type: str, *, override: bool = False
) -> Callable[[_ResolverClass], _ResolverClass]:
    """Decorator to register a dataset identity resolver class.

    The resolver class must be instantiable without required constructor args.
    """

    def _decorator(resolver_cls: _ResolverClass) -> _ResolverClass:
        register_dataset_identity_resolver(dataset_type, resolver_cls, override=override)
        return resolver_cls

    return _decorator


def _normalize_dataset_type(dataset_type: str | None) -> str | None:
    if not dataset_type:
        return None
    normalized = dataset_type.strip().lower()
    return normalized or None


def _resolver_score(resolver: DatasetIdentityResolver, identity: DatasetIdentity) -> tuple[float, int]:
    confidence = identity.confidence if identity.confidence is not None else _DEFAULT_CONFIDENCE
    priority = int(getattr(resolver, "priority", _DEFAULT_PRIORITY))
    return confidence, -priority


def _resolve_with_registry(dataset: xr.Dataset) -> DatasetIdentity | None:
    resolvers = sorted(
        _RESOLVERS.values(), key=lambda r: int(getattr(r, "priority", _DEFAULT_PRIORITY))
    )
    candidates: list[tuple[DatasetIdentityResolver, DatasetIdentity]] = []

    for resolver in resolvers:
        identity = resolver.evaluate(dataset)
        if identity is None:
            continue
        normalized_dataset_type = _normalize_dataset_type(resolver.dataset_type) or _normalize_dataset_type(
            identity.dataset_type
        )
        candidate = DatasetIdentity(
            dataset_type=normalized_dataset_type,
            dataset_id=identity.dataset_id,
            project_id=identity.project_id,
            confidence=identity.confidence,
            evidence=tuple(identity.evidence),
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
    fallback_identity = _FALLBACK_RESOLVER.evaluate(dataset)
    if fallback_identity is None:
        raise RuntimeError("fallback resolver did not return an identity")
    return fallback_identity
