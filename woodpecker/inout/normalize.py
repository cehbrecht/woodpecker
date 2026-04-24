from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List

from .base import DataInput
from .detect import detect_path_kind, is_pathlike, is_xarray_object
from .folder import FolderInput
from .nc import NetCDFInput, NetCDFOutputAdapter
from .runtime import _zarr_backend_available, warn_once
from .xr import XarrayInput
from .zarr import ZarrInput, ZarrOutputAdapter


def get_output_adapter(output_format: str | None = None):
    if output_format in (None, "", "auto"):
        return None
    normalized = output_format.lower()
    if normalized in ("netcdf", "nc"):
        adapter = NetCDFOutputAdapter()
        if not adapter.is_available:
            warn_once("NetCDF output format requested but no NetCDF backend is available.")
        return adapter
    if normalized == "zarr":
        adapter = ZarrOutputAdapter()
        if not adapter.is_available:
            warn_once("Zarr output format requested but zarr backend is not available.")
        return adapter
    raise ValueError(f"Unsupported output format: {output_format}")


def _as_data_input(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return value.expand()

    if is_pathlike(value):
        path = Path(value)
        path_kind = detect_path_kind(path)
        if path_kind == "netcdf-directory":
            return FolderInput(source_path=path, name=path.name).expand()
        if path_kind == "zarr":
            if not _zarr_backend_available():
                warn_once(
                    f"Zarr input '{path}' requested but zarr backend is not available."
                    " Processing will continue with safe fallback behavior."
                )
            return [ZarrInput(source_path=path, name=path.name)]
        if path_kind == "netcdf":
            return [NetCDFInput(source_path=path, name=path.name)]
        raise ValueError(f"Unsupported path input: {path}")

    if is_xarray_object(value):
        return [XarrayInput(payload=value)]

    raise TypeError(f"Unsupported input type: {type(value)!r}")


def normalize_inputs(inputs: Any) -> List[DataInput]:
    if is_pathlike(inputs) or is_xarray_object(inputs) or isinstance(inputs, DataInput):
        return _as_data_input(inputs)

    if isinstance(inputs, Iterable):
        normalized: List[DataInput] = []
        for item in inputs:
            normalized.extend(_as_data_input(item))
        return normalized

    return _as_data_input(inputs)
