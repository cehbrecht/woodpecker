from __future__ import annotations

import xarray as xr

_CELSIUS_UNITS = {"c", "degc", "degreec", "degreesc", "celsius"}


def normalized_unit(unit: str) -> str:
    return unit.strip().lower().replace(" ", "").replace("_", "")


def is_celsius_unit(unit: str | None) -> bool:
    if not isinstance(unit, str) or not unit.strip():
        return False
    return normalized_unit(unit) in _CELSIUS_UNITS


def get_data_unit(dataset: xr.Dataset, variable_name: str) -> str | None:
    if variable_name not in dataset.data_vars:
        return None
    variable = dataset[variable_name]
    attr_units = variable.attrs.get("units")
    if isinstance(attr_units, str) and attr_units.strip():
        return attr_units
    encoding_units = variable.encoding.get("units")
    if isinstance(encoding_units, str) and encoding_units.strip():
        return encoding_units
    return None


def target_temperature_variable(dataset: xr.Dataset) -> str | None:
    for candidate in ("tas", "temp"):
        if candidate in dataset.data_vars:
            return candidate
    return None


def first_str_attr(dataset: xr.Dataset, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = dataset.attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def project_id_from_dataset(dataset: xr.Dataset) -> str:
    dataset_id = first_str_attr(dataset, ("dataset_id", "ds_id", "id", "source_id", "source_name"))
    if not dataset_id:
        return ""
    return dataset_id.split(".", 1)[0]
