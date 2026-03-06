from __future__ import annotations

import importlib.util
import warnings
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


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _netcdf_backend_available() -> bool:
    return any(_module_available(name) for name in ("netCDF4", "h5netcdf", "scipy"))


def _zarr_backend_available() -> bool:
    return all(_module_available(name) for name in ("zarr", "numcodecs"))


def get_io_availability() -> dict[str, bool]:
    netcdf_available = _netcdf_backend_available()
    zarr_available = _zarr_backend_available()
    return {
        "xarray_input": True,
        "netcdf_input": netcdf_available,
        "zarr_input": zarr_available,
        "netcdf_output": netcdf_available,
        "zarr_output": zarr_available,
    }


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
    def is_available(self) -> bool:
        return True

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

    @property
    def is_available(self) -> bool:
        return _netcdf_backend_available()

    def load(self) -> xr.Dataset:
        if not self.is_available:
            warnings.warn(
                f"NetCDF input backend unavailable for '{self.reference}'. Falling back to empty dataset.",
                stacklevel=2,
            )
            dataset = xr.Dataset()
            dataset.attrs.setdefault("source_name", self.source_name)
            return dataset
        try:
            dataset = xr.open_dataset(self.source_path)
        except Exception as exc:
            warnings.warn(
                f"Failed to read NetCDF input '{self.reference}': {exc}. Falling back to empty dataset.",
                stacklevel=2,
            )
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
        if not self.is_available:
            warnings.warn(
                f"NetCDF output backend unavailable for '{self.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        try:
            dataset.to_netcdf(self.source_path)
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write NetCDF output '{self.reference}': {exc}.",
                stacklevel=2,
            )
            return False


@dataclass
class ZarrInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    @property
    def is_available(self) -> bool:
        return _zarr_backend_available()

    def load(self) -> xr.Dataset:
        if not self.is_available:
            warnings.warn(
                f"Zarr input backend unavailable for '{self.reference}'. Falling back to empty dataset.",
                stacklevel=2,
            )
            dataset = xr.Dataset()
            dataset.attrs.setdefault("source_name", self.source_name)
            return dataset
        try:
            dataset = xr.open_zarr(self.source_path)
        except Exception as exc:
            warnings.warn(
                f"Failed to read Zarr input '{self.reference}': {exc}. Falling back to empty dataset.",
                stacklevel=2,
            )
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
        if not self.is_available:
            warnings.warn(
                f"Zarr output backend unavailable for '{self.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        try:
            dataset.to_zarr(self.source_path, mode="w")
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write Zarr output '{self.reference}': {exc}.",
                stacklevel=2,
            )
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

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    def target_path(self, data_input: DataInput) -> Path:
        pass

    @abstractmethod
    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        pass


class NetCDFOutputAdapter(OutputAdapter):
    format_name = "netcdf"

    @property
    def is_available(self) -> bool:
        return _netcdf_backend_available()

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("NetCDF output requires a path-based input")
        return data_input.source_path.with_suffix(".nc")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        if not self.is_available:
            warnings.warn(
                f"NetCDF output backend unavailable for '{data_input.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        target = self.target_path(data_input)
        try:
            dataset.to_netcdf(target)
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write NetCDF output '{target}': {exc}.",
                stacklevel=2,
            )
            return False


class ZarrOutputAdapter(OutputAdapter):
    format_name = "zarr"

    @property
    def is_available(self) -> bool:
        return _zarr_backend_available()

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("Zarr output requires a path-based input")
        return data_input.source_path.with_suffix(".zarr")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        if not self.is_available:
            warnings.warn(
                f"Zarr output backend unavailable for '{data_input.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        target = self.target_path(data_input)
        try:
            dataset.to_zarr(target, mode="w")
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write Zarr output '{target}': {exc}.",
                stacklevel=2,
            )
            return False


def get_output_adapter(output_format: str | None = None) -> OutputAdapter | None:
    if output_format in (None, "", "auto"):
        return None
    normalized = output_format.lower()
    if normalized in ("netcdf", "nc"):
        adapter = NetCDFOutputAdapter()
        if not adapter.is_available:
            warnings.warn(
                "NetCDF output format requested but no NetCDF backend is available.",
                stacklevel=2,
            )
        return adapter
    if normalized == "zarr":
        adapter = ZarrOutputAdapter()
        if not adapter.is_available:
            warnings.warn(
                "Zarr output format requested but zarr backend is not available.",
                stacklevel=2,
            )
        return adapter
    raise ValueError(f"Unsupported output format: {output_format}")


def _as_data_input(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return value.expand()

    if _is_pathlike(value):
        path = Path(value)
        if path.is_dir():
            return FolderInput(source_path=path, name=path.name).expand()
        if path.suffix.lower() == ".zarr":
            if not _zarr_backend_available():
                warnings.warn(
                    f"Zarr input '{path}' requested but zarr backend is not available."
                    " Processing will continue with safe fallback behavior.",
                    stacklevel=2,
                )
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
