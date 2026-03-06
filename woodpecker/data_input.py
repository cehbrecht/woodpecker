from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, Iterable, List, Sequence

import xarray as xr


def _is_xarray_object(value: Any) -> bool:
    return isinstance(value, (xr.Dataset, xr.DataArray))


def _is_pathlike(value: Any) -> bool:
    return isinstance(value, (str, PathLike, Path))


@dataclass
class DataInput(ABC):
    source_path: Path | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def load(self) -> xr.Dataset:
        pass

    def save(
        self,
        dataset: xr.Dataset,
        dry_run: bool = True,
        output_adapter: OutputAdapter | None = None,
    ) -> bool:
        return not dry_run

    def expand(self) -> list[DataInput]:
        return [self]

    @property
    def source_name(self) -> str:
        if self.source_path is not None:
            return self.source_path.name
        if self.name:
            return self.name

        payload = getattr(self, "payload", None)
        attrs = getattr(payload, "attrs", None)
        if isinstance(attrs, dict):
            for key in ("source_name", "name", "id"):
                value = attrs.get(key)
                if isinstance(value, str) and value:
                    return value

        payload_name = getattr(payload, "name", None)
        if isinstance(payload_name, str) and payload_name:
            return payload_name

        return "<in-memory>"

    @property
    def reference(self) -> str:
        if self.source_path is not None:
            return str(self.source_path)
        return self.source_name


@dataclass
class XarrayInput(DataInput):
    payload: xr.Dataset | xr.DataArray | None = None

    def load(self) -> xr.Dataset:
        if self.payload is None:
            raise ValueError("XarrayInput payload is required")
        if isinstance(self.payload, xr.DataArray):
            return self.payload.to_dataset(name=self.payload.name or "value")
        return self.payload


@dataclass
class PathInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    def load(self) -> xr.Dataset:
        try:
            dataset = xr.open_dataset(self.source_path)
        except Exception:
            dataset = xr.Dataset()
        dataset.attrs.setdefault("source_name", self.source_name)
        return dataset

    def save(
        self,
        dataset: xr.Dataset,
        dry_run: bool = True,
        output_adapter: OutputAdapter | None = None,
    ) -> bool:
        if output_adapter is not None:
            return output_adapter.save(dataset, self, dry_run=dry_run)
        if dry_run:
            return False
        try:
            dataset.to_netcdf(self.source_path)
            return True
        except Exception:
            return False


@dataclass
class ZarrInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    def load(self) -> xr.Dataset:
        try:
            dataset = xr.open_zarr(self.source_path)
        except Exception:
            dataset = xr.Dataset()
        dataset.attrs.setdefault("source_name", self.source_name)
        return dataset

    def save(
        self,
        dataset: xr.Dataset,
        dry_run: bool = True,
        output_adapter: OutputAdapter | None = None,
    ) -> bool:
        if output_adapter is not None:
            return output_adapter.save(dataset, self, dry_run=dry_run)
        if dry_run:
            return False
        try:
            dataset.to_zarr(self.source_path, mode="w")
            return True
        except Exception:
            return False


@dataclass
class FolderInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    def load(self) -> xr.Dataset:
        raise NotImplementedError("FolderInput does not load a single dataset; call expand().")

    def expand(self) -> list[DataInput]:
        return [PathInput(source_path=file_path, name=file_path.name) for file_path in collect_netcdf_files([self.source_path])]


def collect_netcdf_files(paths: Sequence[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".nc":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.nc")))
    return files


class OutputAdapter(ABC):
    format_name: str

    @abstractmethod
    def target_path(self, data_input: DataInput) -> Path:
        pass

    @abstractmethod
    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        pass


class NetCDFOutputAdapter(OutputAdapter):
    format_name = "netcdf"

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("NetCDF output requires a path-based input")
        return data_input.source_path.with_suffix(".nc")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        target = self.target_path(data_input)
        try:
            dataset.to_netcdf(target)
            return True
        except Exception:
            return False


class ZarrOutputAdapter(OutputAdapter):
    format_name = "zarr"

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("Zarr output requires a path-based input")
        return data_input.source_path.with_suffix(".zarr")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        target = self.target_path(data_input)
        try:
            dataset.to_zarr(target, mode="w")
            return True
        except Exception:
            return False


def get_output_adapter(output_format: str | None = None) -> OutputAdapter | None:
    if output_format in (None, "", "auto"):
        return None
    normalized = output_format.lower()
    if normalized in ("netcdf", "nc"):
        return NetCDFOutputAdapter()
    if normalized == "zarr":
        return ZarrOutputAdapter()
    raise ValueError(f"Unsupported output format: {output_format}")


def _as_data_input(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return value.expand()

    if _is_pathlike(value):
        path = Path(value)
        if path.is_dir():
            return FolderInput(source_path=path, name=path.name).expand()
        if path.suffix.lower() == ".zarr":
            return [ZarrInput(source_path=path, name=path.name)]
        if path.is_file() and path.suffix.lower() == ".nc":
            return [PathInput(source_path=path, name=path.name)]
        raise ValueError(f"Unsupported path input: {path}")

    if _is_xarray_object(value):
        return [XarrayInput(payload=value)]

    raise TypeError(f"Unsupported input type: {type(value)!r}")


def normalize_inputs(inputs: Any) -> List[DataInput]:
    if _is_pathlike(inputs) or _is_xarray_object(inputs) or isinstance(inputs, DataInput):
        return _as_data_input(inputs)

    if isinstance(inputs, Iterable):
        normalized: List[DataInput] = []
        for item in inputs:
            normalized.extend(_as_data_input(item))
        return normalized

    return _as_data_input(inputs)
