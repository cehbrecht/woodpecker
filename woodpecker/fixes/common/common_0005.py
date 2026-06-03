from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any

import xarray as xr

from ..registry import FixFunction, FixFunctionRegistry


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        return ()

    out: list[str] = []
    for item in values:
        name = str(item).strip()
        if name and name not in out:
            out.append(name)
    return tuple(out)


def _mapping_from_config(config: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    raw = config.get("mapping", {})
    if not isinstance(raw, Mapping):
        return {}

    mapping: dict[str, tuple[str, ...]] = {}
    for target, candidates in raw.items():
        target_name = str(target).strip()
        candidate_names = _as_string_tuple(candidates)
        if target_name and candidate_names:
            mapping[target_name] = candidate_names
    return mapping


def _overwrite_dataset_in_place(target: xr.Dataset, source: xr.Dataset) -> None:
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


def _dataset_changed(before: xr.Dataset, after: xr.Dataset) -> bool:
    return not before.identical(after)


class DatasetTransform(FixFunction):
    message = "dataset can be normalized"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        return dataset

    def matches(self, dataset: xr.Dataset) -> bool:
        return _dataset_changed(dataset, self.transform(dataset))

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not self.matches(dataset):
            return []
        return [self.message]

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        transformed = self.transform(dataset)
        if not _dataset_changed(dataset, transformed):
            return False
        if dry_run:
            return True
        _overwrite_dataset_in_place(dataset, transformed)
        return True


def _maybe_rename_dims(data_array: xr.DataArray, mapping: Mapping[str, tuple[str, ...]]):
    for dim in data_array.dims:
        for target, candidates in mapping.items():
            if dim not in candidates or target in data_array.dims:
                continue
            data_array = data_array.swap_dims({dim: target})
            if dim in data_array.coords and dim != target:
                data_array = data_array.assign_coords({target: data_array[dim].rename(target)})
                data_array = data_array.drop_vars(dim)
    return data_array


def _rename_variables(dataset: xr.Dataset, mapping: Mapping[str, tuple[str, ...]]) -> xr.Dataset:
    if not mapping:
        return dataset

    attrs = dict(dataset.attrs)
    encoding = dict(dataset.encoding)
    renamed = xr.Dataset(
        {
            name: _maybe_rename_dims(dataset[name], mapping)
            for name in list(dataset.data_vars) + list(set(dataset.coords) - set(dataset.dims))
        },
        attrs=attrs,
    )
    renamed.encoding = encoding

    rename_vars = list(set(renamed.variables) - set(renamed.dims))
    for target, candidates in mapping.items():
        if target in renamed:
            continue
        matching_candidates = [candidate for candidate in candidates if candidate in rename_vars]
        if matching_candidates:
            renamed = renamed.rename({matching_candidates[0]: target})

    renamed.attrs = attrs
    renamed.encoding = encoding
    return renamed


@FixFunctionRegistry.register
class RenameVariables(DatasetTransform):
    name = "Rename variables and dimensions"
    description = "Renames variables, coordinates, and dimensions from configured candidate names."
    categories = ["structure"]
    priority = 33
    dataset = None
    labels = ["risk.safe.reversible_rename"]
    message = "variables, coordinates, or dimensions can be renamed"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        mapping = _mapping_from_config(getattr(self, "config", {}) or {})
        return _rename_variables(dataset, mapping)


@FixFunctionRegistry.register
class PromoteMissingDimensionCoords(DatasetTransform):
    name = "Promote missing dimension coordinates"
    description = "Creates coordinate variables for dimensions that have no coordinate."
    categories = ["structure"]
    priority = 34
    dataset = None
    labels = ["risk.safe.coordinate_creation"]
    message = "dimensions without coordinate variables can be promoted"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        config = getattr(self, "config", {}) or {}
        configured_dims = _as_string_tuple(config.get("dims"))
        dims = configured_dims or tuple(dataset.dims)

        transformed = dataset.copy()
        for dim in dims:
            if dim in transformed.dims and dim not in transformed.coords:
                transformed = transformed.assign_coords({dim: transformed[dim]})
        return transformed


@FixFunctionRegistry.register
class SetCoordinateVariables(DatasetTransform):
    name = "Set coordinate variables"
    description = "Moves configured variables into the coordinate set."
    categories = ["structure", "metadata"]
    priority = 35
    dataset = None
    labels = ["risk.safe.metadata_only"]
    message = "configured variables can be marked as coordinates"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        config = getattr(self, "config", {}) or {}
        coordinates = _as_string_tuple(config.get("coordinates") or config.get("coords"))
        if not coordinates:
            return dataset

        transformed = dataset.copy()
        for coordinate in coordinates:
            if coordinate in transformed.variables and coordinate not in transformed.coords:
                transformed = transformed.set_coords(coordinate)
        return transformed


def _normalize_unit_name(unit: object) -> str:
    return str(unit or "").strip().lower().replace(" ", "_")


def _convert_to_meters(data_array: xr.DataArray) -> xr.DataArray | None:
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


def _convert_units_with_pint(
    dataset: xr.Dataset,
    target_units: Mapping[str, str],
    unit_overrides: Mapping[str, str | None],
) -> xr.Dataset:
    import cf_xarray.units  # noqa: F401
    import pint  # noqa: F401
    import pint_xarray  # noqa: F401

    quantified = dataset.pint.quantify(dict(unit_overrides))
    available_targets = {
        variable: target_unit
        for variable, target_unit in target_units.items()
        if variable in quantified.variables
    }
    converted = quantified.pint.to(available_targets)
    return converted.pint.dequantify(format="~P")


@FixFunctionRegistry.register
class ConvertUnits(DatasetTransform):
    name = "Convert variable units"
    description = "Converts configured variables or coordinates to target units."
    categories = ["metadata", "units"]
    priority = 36
    dataset = None
    labels = ["risk.careful.value_transformation"]
    message = "configured variable units can be converted"

    def _target_units(self) -> dict[str, str]:
        config = getattr(self, "config", {}) or {}
        raw = config.get("units", {})
        if not isinstance(raw, Mapping):
            return {}
        return {str(name): str(unit) for name, unit in raw.items() if str(name).strip()}

    def _unit_overrides(self) -> dict[str, str | None]:
        config = getattr(self, "config", {}) or {}
        raw = config.get("overrides", {})
        if not isinstance(raw, Mapping):
            return {}
        return {str(name): (None if unit is None else str(unit)) for name, unit in raw.items()}

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        target_units = {
            variable: target_unit
            for variable, target_unit in self._target_units().items()
            if variable in dataset.variables
        }
        if not target_units:
            return dataset
        if all(
            dataset[variable].attrs.get("units") == target_unit
            for variable, target_unit in target_units.items()
        ):
            return dataset

        pint_error: ValueError | None = None
        try:
            return _convert_units_with_pint(dataset, target_units, self._unit_overrides())
        except ImportError:
            pass
        except ValueError as exc:
            pint_error = exc

        transformed = dataset.copy()
        changed = False
        for variable, target_unit in target_units.items():
            if target_unit != "m":
                continue
            converted = _convert_to_meters(transformed[variable])
            if converted is None:
                continue
            transformed[variable] = converted
            changed = True
        if changed:
            return transformed

        if pint_error is not None:
            warnings.warn(f"Unit conversion failed with: {pint_error}", UserWarning, stacklevel=2)
        return dataset


def _normalize_longitude_values(data_array: xr.DataArray, target: str, mask_abs_gt: float | None):
    values = data_array
    if mask_abs_gt is not None:
        values = values.where(abs(values) <= mask_abs_gt)
    if target == "0_360":
        return values.where(values >= 0, 360 + values)
    if target == "-180_180":
        return ((values + 180) % 360) - 180
    return values


@FixFunctionRegistry.register
class NormalizeLongitudeConvention(DatasetTransform):
    name = "Normalize longitude convention"
    description = "Wraps configured longitude coordinates to a target convention."
    categories = ["coordinates"]
    priority = 37
    dataset = None
    labels = ["risk.careful.coordinate_transformation"]
    message = "longitudes can be wrapped to the configured convention"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        config = getattr(self, "config", {}) or {}
        coordinate = str(config.get("coordinate", "lon")).strip() or "lon"
        target = str(config.get("target", "0_360")).strip() or "0_360"
        bounds = _as_string_tuple(config.get("bounds"))
        mask_abs_gt = config.get("mask_abs_gt", 1000)
        mask_value = None if mask_abs_gt is None else float(mask_abs_gt)

        if coordinate not in dataset.variables:
            return dataset
        if target not in {"0_360", "-180_180"}:
            return dataset

        transformed = dataset.copy()
        transformed = transformed.assign_coords(
            {coordinate: _normalize_longitude_values(transformed[coordinate], target, mask_value)}
        )
        for bounds_name in bounds:
            if bounds_name in transformed.variables:
                transformed = transformed.assign_coords(
                    {
                        bounds_name: _normalize_longitude_values(
                            transformed[bounds_name], target, mask_value
                        )
                    }
                )
        return transformed


@FixFunctionRegistry.register
class DropVariables(DatasetTransform):
    name = "Drop variables"
    description = "Drops configured variables or coordinates."
    categories = ["structure"]
    priority = 38
    dataset = None
    labels = ["risk.careful.variable_removal"]
    message = "configured variables can be dropped"

    def transform(self, dataset: xr.Dataset) -> xr.Dataset:
        config = getattr(self, "config", {}) or {}
        variables = _as_string_tuple(config.get("variables") or config.get("names"))
        if not variables:
            return dataset
        errors = str(config.get("errors", "ignore"))
        if errors not in {"ignore", "raise"}:
            errors = "ignore"
        return dataset.drop_vars(variables, errors=errors)
