from __future__ import annotations

import warnings
from collections.abc import Mapping

import numpy as np
import xarray as xr

DROP_COORDS = ("bnds", "vertex")
DESIRED_UNITS = {"lev": "m"}
UNIT_OVERRIDES = {"so": None}


def is_cmip6_dataset(dataset: xr.Dataset) -> bool:
    explicit_project_tokens = (dataset.attrs.get("project_id"), dataset.attrs.get("mip_era"))
    if any(token is not None for token in explicit_project_tokens) and not any(
        "cmip6" in str(token).lower() for token in explicit_project_tokens if token is not None
    ):
        return False

    project_tokens = (
        dataset.attrs.get("project_id"),
        dataset.attrs.get("mip_era"),
        dataset.attrs.get("dataset_id"),
        dataset.attrs.get("source_file"),
        dataset.attrs.get("source_name"),
    )
    if any("cmip6" in str(token).lower() for token in project_tokens if token is not None):
        return True

    required_cmip6_attrs = ("source_id", "experiment_id", "variant_label", "table_id", "grid_label")
    if not all(dataset.attrs.get(attr) for attr in required_cmip6_attrs):
        return False

    variant_label = str(dataset.attrs.get("variant_label", ""))
    return (
        variant_label.startswith("r")
        and "i" in variant_label
        and "p" in variant_label
        and "f" in variant_label
    )


def cmip6_renaming_dict() -> dict[str, list[str]]:
    return {
        "x": ["i", "ni", "xh", "nlon"],
        "y": ["j", "nj", "yh", "nlat"],
        "lev": ["deptht", "olevel", "zlev", "olev", "depth"],
        "bnds": ["bnds", "axis_nbounds", "d2"],
        "vertex": ["vertex", "nvertex", "vertices", "nvertices"],
        "lon": ["longitude", "nav_lon"],
        "lat": ["latitude", "nav_lat"],
        "lev_bounds": ["deptht_bounds", "lev_bnds", "olevel_bounds", "zlev_bnds"],
        "lon_bounds": [
            "bounds_lon",
            "bounds_nav_lon",
            "lon_bnds",
            "x_bnds",
            "vertices_longitude",
            "longitude_bnds",
        ],
        "lat_bounds": [
            "bounds_lat",
            "bounds_nav_lat",
            "lat_bnds",
            "y_bnds",
            "vertices_latitude",
            "latitude_bnds",
        ],
        "time_bounds": ["time_bnds"],
    }


def _maybe_rename_dims(data_array: xr.DataArray, rename_dict: Mapping[str, list[str]]):
    for dim in data_array.dims:
        for target, candidates in rename_dict.items():
            if dim not in candidates:
                continue
            data_array = data_array.swap_dims({dim: target})
            if dim in data_array.coords and dim != target:
                data_array = data_array.assign_coords({target: data_array[dim].rename(target)})
                data_array = data_array.drop_vars(dim)
    return data_array


def rename_cmip6(dataset: xr.Dataset, rename_dict: Mapping[str, list[str]] | None = None):
    attrs = dict(dataset.attrs)
    encoding = dict(dataset.encoding)
    rename_dict = rename_dict or cmip6_renaming_dict()

    dataset = xr.Dataset(
        {
            name: _maybe_rename_dims(dataset[name], rename_dict)
            for name in list(dataset.data_vars) + list(set(dataset.coords) - set(dataset.dims))
        },
        attrs=attrs,
    )
    dataset.encoding = encoding

    rename_vars = list(set(dataset.variables) - set(dataset.dims))
    for target, candidates in rename_dict.items():
        if target in dataset:
            continue
        matching_candidates = [candidate for candidate in candidates if candidate in rename_vars]
        if matching_candidates:
            dataset = dataset.rename({matching_candidates[0]: target})

    for dim, coord in (("x", "lon"), ("y", "lat")):
        if dim not in dataset.dims and coord in dataset.dims:
            dataset = dataset.rename({coord: dim})

    dataset.attrs = attrs
    dataset.encoding = encoding
    return dataset


def promote_empty_dims(dataset: xr.Dataset):
    dataset = dataset.copy()
    for dim in dataset.dims:
        if dim not in dataset.coords:
            dataset = dataset.assign_coords({dim: dataset[dim]})
    return dataset


def correct_coordinates(dataset: xr.Dataset):
    dataset = dataset.copy()
    for coord in (
        "x",
        "y",
        "lon",
        "lat",
        "lev",
        "bnds",
        "lev_bounds",
        "lon_bounds",
        "lat_bounds",
        "time_bounds",
        "lat_verticies",
        "lon_verticies",
    ):
        if coord in dataset.variables:
            dataset = dataset.set_coords(coord)
    return dataset


def broadcast_lonlat(dataset: xr.Dataset):
    dataset = dataset.copy()
    if "lon" not in dataset.variables and "x" in dataset.variables:
        dataset.coords["lon"] = dataset["x"]
    if "lat" not in dataset.variables and "y" in dataset.variables:
        dataset.coords["lat"] = dataset["y"]

    if "lon" in dataset.variables and "lat" in dataset.variables:
        if len(dataset["lon"].dims) < 2:
            dataset.coords["lon"] = dataset["lon"] * xr.ones_like(dataset["lat"])
        if len(dataset["lat"].dims) < 2:
            dataset.coords["lat"] = xr.ones_like(dataset["lon"]) * dataset["lat"]
    return dataset


def _interp_nominal_lon(lon_1d: np.ndarray) -> np.ndarray:
    x = np.arange(len(lon_1d))
    idx = np.isnan(lon_1d)
    return np.interp(x, x[~idx], lon_1d[~idx], period=len(lon_1d))


def _fix_non_unique(values: np.ndarray, *, pad: bool = False) -> np.ndarray:
    values = np.array(values, copy=True)
    if len(values) == len(np.unique(values)):
        return values

    if pad:
        if len(np.unique(values[0:2])) < 2:
            values[0] = -90
        if len(np.unique(values[-2:])) < 2:
            values[-1] = 90

    index_range = np.arange(len(values))
    _, unique_indices = np.unique(values, return_index=True)
    duplicate_index = np.array([index not in unique_indices for index in index_range])
    values[duplicate_index] = np.interp(
        index_range[duplicate_index],
        index_range[~duplicate_index],
        values[~duplicate_index],
    )
    return values


def replace_x_y_nominal_lat_lon(dataset: xr.Dataset):
    """Approximate x/y coordinate values from representative lon/lat slices."""

    required = {"x", "y"}
    if not required.issubset(dataset.dims):
        return dataset
    if "lon" not in dataset.variables or "lat" not in dataset.variables:
        return dataset
    if "x" not in dataset["lon"].dims or "y" not in dataset["lat"].dims:
        return dataset

    dataset = dataset.copy()
    eq_idx = len(dataset.y) // 2

    nominal_x = dataset.isel(y=eq_idx).lon.load()
    nominal_y = dataset.lat.max("x").load()

    nominal_x_values = _interp_nominal_lon(np.asarray(nominal_x.data, dtype=float))
    nominal_y_values = nominal_y.interpolate_na("y").data

    dataset = dataset.assign_coords(
        x=_fix_non_unique(nominal_x_values),
        y=_fix_non_unique(nominal_y_values),
    )
    dataset = dataset.sortby("x")
    dataset = dataset.sortby("y")

    return dataset.assign_coords(
        x=_fix_non_unique(dataset.x.load().data),
        y=_fix_non_unique(dataset.y.load().data, pad=True),
    )


def _normalize_unit_name(unit: object) -> str:
    return str(unit or "").strip().lower().replace(" ", "_")


def _convert_data_array_to_meters(data_array: xr.DataArray) -> xr.DataArray | None:
    unit = _normalize_unit_name(data_array.attrs.get("units"))
    if unit in {"m", "meter", "meters", "metre", "metres"}:
        if data_array.attrs.get("units") == "m":
            return None
        converted = data_array.copy()
        converted.attrs = dict(data_array.attrs)
        converted.attrs["units"] = "m"
        return converted
    if unit in {"cm", "centimeter", "centimeters", "centimetre", "centimetres"}:
        converted = data_array / 100.0
        converted.attrs = dict(data_array.attrs)
        converted.attrs["units"] = "m"
        return converted
    return None


def _correct_units_with_pint(dataset: xr.Dataset) -> xr.Dataset:
    import cf_xarray.units  # noqa: F401
    import pint  # noqa: F401
    import pint_xarray  # noqa: F401

    quantified = dataset.pint.quantify(UNIT_OVERRIDES)
    target_units = {
        variable: target_unit
        for variable, target_unit in DESIRED_UNITS.items()
        if variable in quantified
    }
    converted = quantified.pint.to(target_units)
    return converted.pint.dequantify(format="~P")


def correct_units(dataset: xr.Dataset):
    if not any(variable in dataset.variables for variable in DESIRED_UNITS):
        return dataset
    if all(
        variable not in dataset.variables or dataset[variable].attrs.get("units") == target_unit
        for variable, target_unit in DESIRED_UNITS.items()
    ):
        return dataset

    pint_error: ValueError | None = None
    try:
        return _correct_units_with_pint(dataset)
    except ImportError:
        pass
    except ValueError as exc:
        pint_error = exc

    converted = dataset.copy()
    changed = False
    for variable, target_unit in DESIRED_UNITS.items():
        if target_unit != "m" or variable not in converted.variables:
            continue
        converted_variable = _convert_data_array_to_meters(converted[variable])
        if converted_variable is None:
            continue
        converted[variable] = converted_variable
        changed = True
    if changed:
        return converted

    if pint_error is not None:
        warnings.warn(f"Unit correction failed with: {pint_error}", UserWarning, stacklevel=2)
    return dataset


def parse_lon_lat_bounds(dataset: xr.Dataset):
    dataset = dataset.copy()

    if "lat_bounds" in dataset.variables and "x" in dataset.variables:
        if "x" not in dataset.lat_bounds.dims:
            dataset.coords["lat_bounds"] = dataset.coords["lat_bounds"] * xr.ones_like(dataset.x)

    if "lon_bounds" in dataset.variables and "y" in dataset.variables:
        if "y" not in dataset.lon_bounds.dims:
            dataset.coords["lon_bounds"] = dataset.coords["lon_bounds"] * xr.ones_like(dataset.y)

    for error_dim in ("time",):
        for coord in ("lon_bounds", "lat_bounds", "lev_bounds"):
            if coord not in dataset.variables or error_dim not in dataset[coord].dims:
                continue
            stripped_coord = dataset[coord].isel({error_dim: 0}).squeeze()
            if error_dim in stripped_coord.coords:
                stripped_coord = stripped_coord.drop_vars(error_dim)
            dataset = dataset.assign_coords({coord: stripped_coord})

    for variable in ("lon", "lat"):
        bounds_name = f"{variable}_bounds"
        if bounds_name in dataset.variables and "vertex" in dataset[bounds_name].dims:
            dataset = dataset.rename({bounds_name: f"{variable}_verticies"})

    return dataset


def maybe_convert_bounds_to_vertex(dataset: xr.Dataset):
    dataset = dataset.copy()
    if "bnds" not in dataset.dims:
        return dataset
    if "lon_bounds" not in dataset.variables or "lat_bounds" not in dataset.variables:
        return dataset
    if "lon_verticies" in dataset.variables or "lat_verticies" in dataset.variables:
        return dataset

    lon_bounds = xr.ones_like(dataset.lat) * dataset.coords["lon_bounds"]
    lat_bounds = xr.ones_like(dataset.lon) * dataset.coords["lat_bounds"]

    lon_vertices = xr.concat(
        [lon_bounds.isel(bnds=index).squeeze(drop=True) for index in (0, 0, 1, 1)],
        dim="vertex",
    ).reset_coords(drop=True)
    lat_vertices = xr.concat(
        [lat_bounds.isel(bnds=index).squeeze(drop=True) for index in (0, 1, 1, 0)],
        dim="vertex",
    ).reset_coords(drop=True)

    return dataset.assign_coords(lon_verticies=lon_vertices, lat_verticies=lat_vertices)


def maybe_convert_vertex_to_bounds(dataset: xr.Dataset):
    dataset = dataset.copy()
    if "vertex" in dataset.dims:
        if "lon_verticies" in dataset.variables and "lat_verticies" in dataset.variables:
            if "lon_bounds" not in dataset.variables and "lat_bounds" not in dataset.variables:
                lon_bounds = xr.concat(
                    [
                        dataset["lon_verticies"].isel(vertex=[0, 1]).mean("vertex"),
                        dataset["lon_verticies"].isel(vertex=[2, 3]).mean("vertex"),
                    ],
                    dim="bnds",
                )
                lat_bounds = xr.concat(
                    [
                        dataset["lat_verticies"].isel(vertex=[0, 3]).mean("vertex"),
                        dataset["lat_verticies"].isel(vertex=[1, 2]).mean("vertex"),
                    ],
                    dim="bnds",
                )
                dataset = dataset.assign_coords(lon_bounds=lon_bounds, lat_bounds=lat_bounds)
    return promote_empty_dims(dataset)


def sort_vertex_order(dataset: xr.Dataset):
    dataset = dataset.copy()
    required = {"vertex", "x", "y"}
    if not required.issubset(dataset.dims):
        return dataset
    if "lon_verticies" not in dataset.variables or "lat_verticies" not in dataset.variables:
        return dataset

    x_idx = len(dataset.x) // 2
    y_idx = len(dataset.y) // 2
    lon_bounds = dataset.lon_verticies.isel(x=x_idx, y=y_idx).load().data
    lat_bounds = dataset.lat_verticies.isel(x=x_idx, y=y_idx).load().data
    vertices = dataset.vertex.load().data

    points = np.vstack((lon_bounds, lat_bounds, vertices)).T
    lon_sorted = points[np.argsort(points[:, 0]), :]
    right = lon_sorted[:2, :]
    left = lon_sorted[2:, :]
    bottom_left, top_left = left[np.argsort(left[:, 1]), :]
    bottom_right, top_right = right[np.argsort(right[:, 1]), :]
    points_sorted = np.vstack((bottom_left, top_left, top_right, bottom_right))
    idx_sorted = (points_sorted.shape[0] - 1) - np.argsort(points_sorted[:, 2])
    return dataset.assign_coords(vertex=idx_sorted).sortby("vertex")


def fix_metadata(dataset: xr.Dataset):
    dataset = dataset.copy()
    source_id = dataset.attrs.get("source_id")
    experiment_id = dataset.attrs.get("experiment_id")
    if source_id == "GFDL-CM4" and experiment_id in {"1pctCO2", "abrupt-4xCO2", "historical"}:
        dataset.attrs["branch_time_in_parent"] = 91250
    if source_id == "GFDL-CM4" and experiment_id in {"ssp245", "ssp585"}:
        dataset.attrs["branch_time_in_child"] = 60225
    return dataset


def overwrite_dataset_in_place(target: xr.Dataset, source: xr.Dataset) -> None:
    replace = getattr(target, "_replace", None)
    if callable(replace):
        replace(
            variables=source._variables,
            coord_names=source._coord_names,
            dims=source._dims,
            attrs=dict(source.attrs),
            indexes=source._indexes,
            encoding=dict(source.encoding),
            inplace=True,
        )
        return

    target._variables = dict(source._variables)
    target._coord_names = set(source._coord_names)
    target._dims = dict(source._dims)
    target._indexes = dict(source._indexes)
    target.attrs.clear()
    target.attrs.update(source.attrs)
    target.encoding.clear()
    target.encoding.update(source.encoding)


def dataset_changed(before: xr.Dataset, after: xr.Dataset) -> bool:
    return not before.identical(after)
