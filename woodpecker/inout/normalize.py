from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List

from .base import DataInput
from .detect import is_pathlike, is_xarray_object, resolve_input, resolve_output_adapter
from .folder import FolderInput
from .runtime import warn_once

# Canonical format-name aliases resolved before registry lookup.
_FORMAT_ALIASES: dict[str, str] = {"nc": "netcdf"}


def get_output_adapter(output_format: str | None = None):
    if output_format in (None, "", "auto"):
        return None
    canonical = _FORMAT_ALIASES.get(output_format.lower(), output_format.lower())
    adapter = resolve_output_adapter(canonical)
    if adapter is None:
        raise ValueError(f"Unsupported output format: {output_format}")
    if not adapter.is_available:
        warn_once(f"{output_format!r} output format requested but backend is not available.")
    return adapter


def _as_data_input(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return value.expand()

    if is_pathlike(value):
        path = Path(value)
        # Plain directories (not .zarr stores) expand to individual NetCDF inputs.
        if path.is_dir() and path.suffix.lower() != ".zarr":
            return FolderInput(source_path=path, name=path.name).expand()
        data_input = resolve_input(path)
        if data_input is None:
            raise ValueError(f"Unsupported path input: {path}")
        return [data_input]

    data_input = resolve_input(value)
    if data_input is None:
        raise TypeError(f"Unsupported input type: {type(value)!r}")
    return [data_input]


def normalize_inputs(inputs: Any) -> List[DataInput]:
    if is_pathlike(inputs) or is_xarray_object(inputs) or isinstance(inputs, DataInput):
        return _as_data_input(inputs)

    if isinstance(inputs, Iterable):
        normalized: List[DataInput] = []
        for item in inputs:
            normalized.extend(_as_data_input(item))
        return normalized

    return _as_data_input(inputs)
