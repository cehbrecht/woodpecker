from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import xarray as xr


def monthly_time(start: str = "2000-01", periods: int = 12) -> np.ndarray:
    """Create compact monthly time coordinates."""
    return np.arange(
        np.datetime64(start, "M"),
        np.datetime64(start, "M") + np.timedelta64(periods, "M"),
        dtype="datetime64[M]",
    )


def regular_lat_lon(nlat: int = 18, nlon: int = 36) -> tuple[np.ndarray, np.ndarray]:
    """Create small global latitude/longitude coordinates."""
    lat = np.linspace(-85.0, 85.0, nlat)
    lon = np.linspace(0.0, 350.0, nlon)
    return lat, lon


def climate_field(
    *,
    variable: str,
    units: str,
    time: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    seed: int | None = None,
) -> xr.DataArray:
    """Create a deterministic, climate-like monthly field.

    A seed adds repeatable perturbations; without a seed the output is fully
    deterministic and contains no pseudo-random component.
    """
    month = np.arange(time.size, dtype=float)[:, None, None]
    lat2d = lat[None, :, None]
    lon2d = lon[None, None, :]

    if variable.startswith("pr"):
        data = 2.0 + 1.5 * np.cos(np.deg2rad(lat2d)) + 0.4 * np.sin(month / 12.0 * 2.0 * np.pi)
        data = np.broadcast_to(data, (time.size, lat.size, lon.size)).copy()
    elif variable in {"tos", "siconc"}:
        data = 285.0 - 0.35 * np.abs(lat2d) + 1.2 * np.cos(np.deg2rad(lon2d - 210.0))
        data = data + 0.5 * np.sin(month / 12.0 * 2.0 * np.pi)
    else:
        data = 288.0 - 0.55 * np.abs(lat2d) + 10.0 * np.cos(month / 12.0 * 2.0 * np.pi)
        data = data + 0.8 * np.sin(np.deg2rad(lon2d))

    if seed is not None:
        rng = np.random.default_rng(seed)
        data = data + rng.normal(0.0, 0.05, size=data.shape)

    return xr.DataArray(
        data.astype("float32"),
        dims=("time", "lat", "lon"),
        coords={"time": time, "lat": lat, "lon": lon},
        name=variable,
        attrs={"standard_name": standard_name_for(variable), "units": units},
    )


def standard_name_for(variable: str) -> str:
    names = {
        "tas": "air_temperature",
        "tasmax": "air_temperature",
        "tasmin": "air_temperature",
        "tos": "sea_surface_temperature",
        "pr": "precipitation_flux",
    }
    return names.get(variable, variable)


def variable_units(variable: str) -> str:
    units = {
        "tas": "K",
        "tasmax": "K",
        "tasmin": "K",
        "tos": "K",
        "pr": "kg m-2 s-1",
    }
    return units.get(variable, "1")


def dataset_with_attrs(
    variable: str,
    *,
    attrs: Mapping[str, Any],
    seed: int | None = None,
) -> xr.Dataset:
    time = monthly_time()
    lat, lon = regular_lat_lon()
    units = str(attrs.get("units", variable_units(variable)))
    field = climate_field(variable=variable, units=units, time=time, lat=lat, lon=lon, seed=seed)

    dataset = field.to_dataset()
    dataset.attrs.update(dict(attrs))
    dataset["time"].attrs.update({"axis": "T", "standard_name": "time"})
    dataset["lat"].attrs.update({"axis": "Y", "standard_name": "latitude", "units": "degrees_north"})
    dataset["lon"].attrs.update({"axis": "X", "standard_name": "longitude", "units": "degrees_east"})
    return dataset
