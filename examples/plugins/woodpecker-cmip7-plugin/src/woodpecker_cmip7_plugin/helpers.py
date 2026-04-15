from __future__ import annotations

import xarray as xr


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
