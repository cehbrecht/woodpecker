from __future__ import annotations

from dataclasses import replace
from typing import Callable, TypeVar

import xarray as xr

from .base import DatasetIdentity, DatasetIdentityResolver, DefaultDatasetIdentityResolver

_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_FALLBACK = DefaultDatasetIdentityResolver()
_ResolverClass = TypeVar("_ResolverClass", bound=type[DatasetIdentityResolver])
_DEFAULT_PRIORITY = 100
_DEFAULT_CONFIDENCE = 1.0


def _register(
    dataset_type: str, resolver: DatasetIdentityResolver, *, override: bool = False
) -> None:
    """Insert *resolver* into the registry under the normalised *dataset_type* key."""
    key = dataset_type.strip().lower()
    if not key:
        raise ValueError("dataset_type must be a non-empty string")
    if key in _RESOLVERS and not override:
        raise ValueError(f"resolver already registered for '{key}'")
    resolver.dataset_type = key
    _RESOLVERS[key] = resolver


def register_dataset_identity(
    dataset_type: str, *, override: bool = False
) -> Callable[[_ResolverClass], _ResolverClass]:
    """Decorator to register a dataset identity resolver class.

    Usage::

        @register_dataset_identity("my-family")
        class MyResolver(DatasetIdentityResolver):
            ...
    """

    def _decorator(cls: _ResolverClass) -> _ResolverClass:
        _register(dataset_type, cls(), override=override)
        return cls

    return _decorator


def _score(resolver: DatasetIdentityResolver, identity: DatasetIdentity) -> tuple[float, int]:
    """Return a (confidence, -priority) tuple for ranking candidate identities."""
    confidence = identity.confidence if identity.confidence is not None else _DEFAULT_CONFIDENCE
    return confidence, -int(getattr(resolver, "priority", _DEFAULT_PRIORITY))


def _normalize_type(dataset_type: str | None) -> str | None:
    """Return a lowercased, stripped dataset type string, or None if blank."""
    normalized = (dataset_type or "").strip().lower()
    return normalized or None


def _best_match(dataset: xr.Dataset) -> DatasetIdentity | None:
    """Evaluate all registered resolvers and return the highest-scoring match."""
    resolvers = sorted(
        _RESOLVERS.values(),
        key=lambda r: int(getattr(r, "priority", _DEFAULT_PRIORITY)),
    )
    candidates: list[tuple[DatasetIdentityResolver, DatasetIdentity]] = []

    for resolver in resolvers:
        identity = resolver.evaluate(dataset)
        if identity is None:
            continue
        normalized_type = _normalize_type(resolver.dataset_type) or _normalize_type(identity.dataset_type)
        candidates.append((
            resolver,
            replace(identity, dataset_type=normalized_type, metadata=dict(identity.metadata)),
        ))

    if not candidates:
        return None

    _, best = max(candidates, key=lambda item: _score(*item))
    return best


def dataset_type_matches_declared(
    fix_dataset: str | None, detected_dataset_type: str | None
) -> bool:
    if not fix_dataset or not detected_dataset_type:
        return True
    return fix_dataset.strip().lower() == detected_dataset_type.strip().lower()


def resolve_dataset_identity(dataset: xr.Dataset) -> DatasetIdentity:
    """Classify a dataset and return its normalized DatasetIdentity.

    Tries all registered resolvers in priority order, chooses the best
    match by (confidence, -priority), and falls back to the generic
    DefaultDatasetIdentityResolver if no resolver matches.
    """
    result = _best_match(dataset)
    if result is not None:
        return result
    fallback = _FALLBACK.evaluate(dataset)
    assert fallback is not None  # DefaultDatasetIdentityResolver always matches
    return fallback
