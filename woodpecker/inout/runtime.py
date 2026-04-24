from __future__ import annotations

import importlib.util
import warnings

_WARNED_MESSAGES: set[str] = set()
_STRICT_IO = False


def warn_once(message: str) -> None:
    if message in _WARNED_MESSAGES:
        return
    _WARNED_MESSAGES.add(message)
    warnings.warn(message, stacklevel=2)


def set_strict_io(strict: bool) -> None:
    global _STRICT_IO
    _STRICT_IO = bool(strict)


def is_strict_io() -> bool:
    return _STRICT_IO


def warn_or_raise(message: str, exc_type: type[Exception] = RuntimeError) -> None:
    if _STRICT_IO:
        raise exc_type(message)
    warn_once(message)


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def netcdf_backend_available() -> bool:
    return any(_module_available(name) for name in ("netCDF4", "h5netcdf", "scipy"))


def _zarr_backend_available() -> bool:
    return all(_module_available(name) for name in ("zarr", "numcodecs"))


def get_io_availability() -> dict[str, bool]:
    netcdf_available = netcdf_backend_available()
    zarr_available = _zarr_backend_available()
    return {
        "xarray_input": True,
        "netcdf_input": netcdf_available,
        "zarr_input": zarr_available,
        "netcdf_output": netcdf_available,
        "zarr_output": zarr_available,
    }
