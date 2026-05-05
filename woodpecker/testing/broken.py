from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr


def apply_corruption(
    dataset: xr.Dataset,
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
) -> xr.Dataset:
    """Return a copy with selected metadata or variable names corrupted."""
    result = dataset.copy(deep=True)

    for name in missing or ():
        result.attrs.pop(name, None)
        for variable in result.data_vars.values():
            variable.attrs.pop(name, None)

    if overrides:
        for name, value in overrides.items():
            result.attrs[name] = value
            if name == "units":
                for variable in result.data_vars.values():
                    variable.attrs[name] = value

    if rename_vars:
        result = result.rename_vars(dict(rename_vars))

    return result
