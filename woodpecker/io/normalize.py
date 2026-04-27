from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List

from .base import DataInput
from .detect import detect_input, is_pathlike, is_xarray_object, resolve_output_adapter
from .directory import DirectoryInput
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


def _is_directory_container(path: Path) -> bool:
    # Keep .zarr directories routed to backend detection as stores.
    return path.is_dir() and path.suffix.lower() != ".zarr"


def _normalize_one(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return value.expand()

    if is_pathlike(value):
        path = Path(value)
        if _is_directory_container(path):
            return DirectoryInput(source_path=path, name=path.name).expand()
        data_input = detect_input(path)
        if data_input is None:
            raise ValueError(f"Unsupported path input: {path}")
        return [data_input]

    data_input = detect_input(value)
    if data_input is None:
        raise TypeError(f"Unsupported input type: {type(value)!r}")
    return [data_input]


def normalize_inputs(inputs: Any) -> List[DataInput]:
    if is_pathlike(inputs) or is_xarray_object(inputs) or isinstance(inputs, DataInput):
        return _normalize_one(inputs)

    if isinstance(inputs, Iterable):
        normalized: List[DataInput] = []
        for item in inputs:
            normalized.extend(_normalize_one(item))
        return normalized

    return _normalize_one(inputs)
