from __future__ import annotations

from typing import ClassVar

import xarray as xr

from woodpecker.fixes.registry import FixFunction, register_fix_function

from .helpers import (
    DROP_COORDS,
    broadcast_lonlat,
    correct_coordinates,
    correct_units,
    dataset_changed,
    fix_metadata,
    is_cmip6_dataset,
    maybe_convert_bounds_to_vertex,
    maybe_convert_vertex_to_bounds,
    overwrite_dataset_in_place,
    parse_lon_lat_bounds,
    rename_cmip6,
    replace_x_y_nominal_lat_lon,
    sort_vertex_order,
)


class XmipCmip6Transform(FixFunction):
    categories: ClassVar[list[str]] = ["structure"]
    priority = 42
    dataset = "CMIP6"
    message: ClassVar[str] = "dataset can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return dataset

    def matches(self, dataset: xr.Dataset) -> bool:
        if not is_cmip6_dataset(dataset):
            return False
        return dataset_changed(dataset, self.transform(dataset))

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not self.matches(dataset):
            return []
        return [self.message]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_dataset(dataset):
            return False

        transformed = self.transform(dataset)
        if not dataset_changed(dataset, transformed):
            return False

        if dry_run:
            return True

        overwrite_dataset_in_place(dataset, transformed)
        return True


@register_fix_function
class RenameCmip6Axes(XmipCmip6Transform):
    suffix = "rename_cmip6_axes"
    name = "Rename CMIP6 axes"
    description = "Normalizes common CMIP6 dimension and coordinate names to x, y, lev, lon, lat, and bounds names."
    categories = ["structure"]
    risk = "safe: reversible rename"
    message = "CMIP6 axes and coordinate names can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return rename_cmip6(dataset)


@register_fix_function
class MarkSpatialCoords(XmipCmip6Transform):
    suffix = "mark_spatial_coords"
    name = "Mark spatial coordinates"
    description = "Moves known spatial, vertical, and bounds variables into the coordinate set."
    categories = ["structure", "metadata"]
    risk = "safe: metadata only"
    message = "known spatial and bounds variables can be marked as coordinates"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return correct_coordinates(dataset)


@register_fix_function
class BroadcastLonLat(XmipCmip6Transform):
    suffix = "broadcast_lon_lat"
    name = "Broadcast lon/lat coordinates"
    description = "Ensures lon and lat coordinates are available as two-dimensional grid coordinates when possible."
    categories = ["structure"]
    risk = "careful: coordinate creation"
    message = "lon/lat coordinates can be broadcast to the model grid"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return broadcast_lonlat(dataset)


@register_fix_function
class NormalizeCoordinateUnits(XmipCmip6Transform):
    suffix = "normalize_coordinate_units"
    name = "Normalize coordinate units"
    description = (
        "Converts supported CMIP6 coordinate units to xMIP target units, currently lev to meters."
    )
    categories = ["metadata", "coordinates"]
    risk = "careful: coordinate transformation"
    message = "supported coordinate units can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return correct_units(dataset)


@register_fix_function
class ReplaceXYWithNominalLonLat(XmipCmip6Transform):
    suffix = "replace_xy_with_nominal_lon_lat"
    name = "Replace x/y with nominal lon/lat"
    description = "Approximates x and y coordinate values from representative lon/lat slices and sorts the grid."
    categories = ["coordinates"]
    risk = "careful: coordinate transformation"
    message = "x/y coordinates can be replaced with nominal lon/lat values"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return replace_x_y_nominal_lat_lon(dataset)


@register_fix_function
class NormalizeLonLatBounds(XmipCmip6Transform):
    suffix = "normalize_lon_lat_bounds"
    name = "Normalize lon/lat bounds"
    description = "Normalizes lon/lat bounds shape and naming, including vertex-style bounds."
    categories = ["structure", "coordinates"]
    risk = "careful: coordinate transformation"
    message = "lon/lat bounds can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return parse_lon_lat_bounds(dataset)


@register_fix_function
class SortVertexOrder(XmipCmip6Transform):
    suffix = "sort_vertex_order"
    name = "Sort vertex order"
    description = "Sorts grid-cell vertices into a consistent lower-left, upper-left, upper-right, lower-right order."
    categories = ["coordinates"]
    risk = "careful: coordinate transformation"
    message = "vertex order can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return sort_vertex_order(dataset)


@register_fix_function
class ConvertBoundsToVertices(XmipCmip6Transform):
    suffix = "convert_bounds_to_vertices"
    name = "Convert bounds to vertices"
    description = "Creates rectangular lon/lat vertex coordinates from lon/lat bounds when vertices are missing."
    categories = ["structure", "coordinates"]
    risk = "careful: coordinate creation"
    message = "lon/lat vertices can be derived from bounds"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return maybe_convert_bounds_to_vertex(dataset)


@register_fix_function
class ConvertVerticesToBounds(XmipCmip6Transform):
    suffix = "convert_vertices_to_bounds"
    name = "Convert vertices to bounds"
    description = (
        "Creates lon/lat bounds from vertex-style lon/lat coordinates when bounds are missing."
    )
    categories = ["structure", "coordinates"]
    risk = "careful: coordinate creation"
    message = "lon/lat bounds can be derived from vertices"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return maybe_convert_vertex_to_bounds(dataset)


@register_fix_function
class KnownCmip6Metadata(XmipCmip6Transform):
    suffix = "fix_known_cmip6_metadata"
    name = "Fix known CMIP6 metadata"
    description = "Applies selected known CMIP6 metadata corrections from xMIP preprocessing."
    categories = ["metadata"]
    risk = "safe: metadata only"
    message = "known CMIP6 metadata corrections can be applied"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return fix_metadata(dataset)


@register_fix_function
class DropHelperGridCoords(XmipCmip6Transform):
    suffix = "drop_helper_grid_coords"
    name = "Drop helper grid coordinates"
    description = "Drops helper bnds and vertex coordinate variables after bounds and vertices are normalized."
    categories = ["structure"]
    risk = "careful: variable removal"
    message = "helper grid coordinates can be dropped"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return dataset.drop_vars(DROP_COORDS, errors="ignore")
