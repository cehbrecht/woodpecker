from __future__ import annotations

from os import PathLike
from pathlib import Path
from types import ModuleType
from typing import Any

import xarray as xr

from .base import DataInput, OutputAdapter
from . import nc as _nc_backend
from . import zarr as _zarr_backend
from . import xr as _xr_backend

# Ordered list of registered backends.  To add a new format, import its
# module here and append it.  No other file needs changing.
_BACKENDS: list[ModuleType] = [_nc_backend, _zarr_backend, _xr_backend]


# ---------------------------------------------------------------------------
# Path/type utilities used by normalize and folder modules
# ---------------------------------------------------------------------------

def is_xarray_object(value: Any) -> bool:
    return isinstance(value, (xr.Dataset, xr.DataArray))


def is_pathlike(value: Any) -> bool:
    return isinstance(value, (str, PathLike, Path))


# ---------------------------------------------------------------------------
# Backend dispatch
# ---------------------------------------------------------------------------

def detect_input(source: Any) -> DataInput | None:
    """Return a DataInput from the first backend that can open *source*, or None."""
    fallback_backend: ModuleType | None = None
    for backend in _BACKENDS:
        if not backend.can_open(source):
            continue
        if backend.is_available():
            return backend.create_input(source)
        if fallback_backend is None:
            fallback_backend = backend
    if fallback_backend is not None:
        return fallback_backend.create_input(source)
    return None


def resolve_input(source: Any) -> DataInput | None:
    return detect_input(source)


def resolve_output_adapter(format_name: str) -> OutputAdapter | None:
    """Return an output adapter for *format_name* from the first matching backend, or None."""
    for backend in _BACKENDS:
        adapter = backend.create_output_adapter()
        if adapter is not None and adapter.format_name == format_name:
            return adapter
    return None
