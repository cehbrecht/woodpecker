from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, List, Sequence

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


def collect_netcdf_files(paths: Sequence[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".nc":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.nc")))
    return files
