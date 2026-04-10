from __future__ import annotations

import xarray as xr


def first_str_attr(dataset: xr.Dataset, keys: tuple[str, ...]) -> str:
    """Return the first non-empty string attribute from the provided keys."""
    for key in keys:
        value = dataset.attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def project_id_from_dataset(dataset: xr.Dataset) -> str:
    """Derive project_id from a dataset identifier-like attribute prefix."""
    dataset_id = first_str_attr(dataset, ("dataset_id", "ds_id", "id", "source_id", "source_name"))
    if not dataset_id:
        return ""
    return dataset_id.split(".", 1)[0]
