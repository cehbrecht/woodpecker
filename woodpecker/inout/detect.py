from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any, Iterable

import xarray as xr

from .base import DataInput


def is_xarray_object(value: Any) -> bool:
    return isinstance(value, (xr.Dataset, xr.DataArray))


def is_pathlike(value: Any) -> bool:
    return isinstance(value, (str, PathLike, Path))


def collect_netcdf_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".nc":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.nc")))
    return files


def detect_path_kind(path: Path) -> str:
    if path.is_dir() and path.suffix.lower() == ".zarr":
        return "zarr"
    if path.is_dir() and collect_netcdf_files([path]):
        return "netcdf-directory"
    if path.is_file() and path.suffix.lower() == ".nc":
        return "netcdf"
    return "unknown"


def detect_input_kind(value: Any) -> str:
    if isinstance(value, DataInput):
        return "data-input"
    if is_xarray_object(value):
        return "xarray"
    if is_pathlike(value):
        return detect_path_kind(Path(value))
    return "unknown"
