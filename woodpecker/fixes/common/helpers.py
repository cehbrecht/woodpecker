from __future__ import annotations

import xarray as xr

_CELSIUS_UNITS = {"c", "degc", "degreec", "degreesc", "celsius"}


def normalized_unit(unit: str) -> str:
    """Normalize a unit string for robust matching."""
    return unit.strip().lower().replace(" ", "").replace("_", "")


def is_celsius_unit(unit: str | None) -> bool:
    """Return True when the unit string represents degrees Celsius."""
    if not isinstance(unit, str) or not unit.strip():
        return False
    return normalized_unit(unit) in _CELSIUS_UNITS


def get_data_unit(dataset: xr.Dataset, variable_name: str) -> str | None:
    """Get a variable unit from attrs first, then encoding."""
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
    """Find the preferred temperature variable name used by shared fixes."""
    for candidate in ("tas", "temp"):
        if candidate in dataset.data_vars:
            return candidate
    return None


def lower_source_name(dataset: xr.Dataset) -> str:
    """Return lower-cased source_name metadata string."""
    return str(dataset.attrs.get("source_name", "")).lower()


def vars_with_encoding_key(
    dataset: xr.Dataset,
    candidates: tuple[str, ...] | list[str],
    key: str,
) -> list[str]:
    """Return variable names whose encoding contains the given key."""
    needs_cleanup: list[str] = []
    for var_name in candidates:
        if var_name not in dataset:
            continue
        if key in dataset[var_name].encoding:
            needs_cleanup.append(var_name)
    return needs_cleanup


def remove_encoding_key(dataset: xr.Dataset, var_names: list[str], key: str) -> bool:
    """Remove an encoding key from selected variables if present."""
    changed = False
    for var_name in var_names:
        if var_name not in dataset:
            continue
        encoding = dataset[var_name].encoding
        if key in encoding:
            del encoding[key]
            changed = True
    return changed


def vars_with_compression_above_level(
    dataset: xr.Dataset,
    candidates: tuple[str, ...] | list[str],
    max_level: int = 1,
) -> list[str]:
    """Return variable names with compression level greater than max_level."""
    matches: list[str] = []
    for var_name in candidates:
        if var_name not in dataset:
            continue
        complevel = dataset[var_name].encoding.get("complevel", 0)
        if isinstance(complevel, (int, float)) and complevel > max_level:
            matches.append(var_name)
    return matches


def normalize_compression_settings(
    dataset: xr.Dataset,
    var_names: list[str],
    level: int = 1,
    zlib: bool = True,
    shuffle: bool = True,
) -> bool:
    """Apply consistent compression encoding settings to selected variables."""
    changed = False
    for var_name in var_names:
        if var_name not in dataset:
            continue
        encoding = dataset[var_name].encoding
        encoding["complevel"] = level
        encoding["zlib"] = zlib
        encoding["shuffle"] = shuffle
        changed = True
    return changed
