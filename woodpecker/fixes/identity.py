from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import xarray as xr


@dataclass(frozen=True)
class DatasetIdentity:
    dataset_id: str
    project_id: str
    dataset_type: str | None = None


class DatasetIdentityResolver(ABC):
    @abstractmethod
    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        pass


class DefaultDatasetIdentityResolver(DatasetIdentityResolver):
    def _first_str_attr(self, dataset: xr.Dataset, keys: tuple[str, ...]) -> str:
        for key in keys:
            value = dataset.attrs.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def dataset_id(self, dataset: xr.Dataset) -> str:
        return self._first_str_attr(
            dataset, ("dataset_id", "ds_id", "id", "source_id", "source_name")
        )

    def project_id(self, dataset: xr.Dataset, dataset_id: str) -> str:
        explicit_project_id = self._first_str_attr(dataset, ("project_id",))
        if explicit_project_id:
            return explicit_project_id
        return project_id_from_dataset_id(dataset_id)

    def resolve(self, dataset: xr.Dataset) -> DatasetIdentity:
        dataset_id = self.dataset_id(dataset)
        project_id = self.project_id(dataset, dataset_id)
        return DatasetIdentity(dataset_id=dataset_id, project_id=project_id, dataset_type=None)


_RESOLVERS: dict[str, DatasetIdentityResolver] = {}
_DEFAULT_RESOLVER = DefaultDatasetIdentityResolver()


def _project_id_from_dataset_id(dataset_id: str) -> str:
    if not dataset_id:
        return ""
    return dataset_id.split(".", 1)[0]


def register_dataset_identity_resolver(
    dataset_type: str, resolver: DatasetIdentityResolver, *, override: bool = False
) -> None:
    key = dataset_type.strip().lower()
    if not key:
        raise ValueError("dataset_type must be a non-empty string")
    if key in _RESOLVERS and not override:
        raise ValueError(f"dataset identity resolver already registered for '{key}'")
    _RESOLVERS[key] = resolver


def resolve_dataset_identity(dataset: xr.Dataset, dataset_type: str | None = None) -> DatasetIdentity:
    if dataset_type:
        key = dataset_type.strip().lower()
        resolver = _RESOLVERS.get(key)
        if resolver is not None:
            identity = resolver.resolve(dataset)
            return DatasetIdentity(
                dataset_id=identity.dataset_id,
                project_id=identity.project_id,
                dataset_type=key,
            )

    identity = _DEFAULT_RESOLVER.resolve(dataset)
    return DatasetIdentity(
        dataset_id=identity.dataset_id,
        project_id=identity.project_id,
        dataset_type=dataset_type.strip().lower() if dataset_type else None,
    )


def project_id_from_dataset_id(dataset_id: str) -> str:
    return _project_id_from_dataset_id(dataset_id)
