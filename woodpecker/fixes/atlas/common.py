from __future__ import annotations

import xarray as xr


def lower_source_name(dataset: xr.Dataset) -> str:
    return str(dataset.attrs.get("source_name", "")).lower()


def atlas_dataset_id(dataset: xr.Dataset) -> str:
    for key in ("ds_id", "dataset_id", "id", "source_id", "source_name"):
        value = dataset.attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def atlas_project_id(dataset: xr.Dataset) -> str:
    ds_id = atlas_dataset_id(dataset)
    if not ds_id:
        return ""
    return ds_id.split(".", 1)[0]


def atlas_vars_to_check(dataset: xr.Dataset) -> list[str]:
    return list(dataset.coords) + list(dataset.data_vars)


def needs_fillvalue_cleanup(dataset: xr.Dataset) -> bool:
    for var in atlas_vars_to_check(dataset):
        if dataset[var].encoding.get("_FillValue", "__missing__") is not None:
            return True
    return False


def needs_string_coord_encoding_cleanup(dataset: xr.Dataset) -> bool:
    coord_vars = (
        "member_id",
        "gcm_variant",
        "gcm_model",
        "gcm_institution",
        "rcm_variant",
        "rcm_model",
        "rcm_institution",
    )
    for var in coord_vars:
        if var not in dataset:
            continue
        enc = dataset[var].encoding
        if any(opt in enc for opt in ("zlib", "shuffle", "complevel")):
            return True
    return False


def needs_compression_level_cleanup(dataset: xr.Dataset) -> bool:
    for var in dataset.data_vars:
        complevel = dataset[var].encoding.get("complevel", 0)
        if isinstance(complevel, (int, float)) and complevel > 1:
            return True
    return False


def needs_project_id(dataset: xr.Dataset) -> bool:
    project_id = atlas_project_id(dataset)
    if not project_id:
        return False
    return dataset.attrs.get("project_id") != project_id


def apply_atlas_encoding_cleanup(dataset: xr.Dataset) -> bool:
    changed = False

    for var in atlas_vars_to_check(dataset):
        if dataset[var].encoding.get("_FillValue", "__missing__") is not None:
            dataset[var].encoding["_FillValue"] = None
            changed = True

    for cvar in (
        "member_id",
        "gcm_variant",
        "gcm_model",
        "gcm_institution",
        "rcm_variant",
        "rcm_model",
        "rcm_institution",
    ):
        if cvar not in dataset:
            continue
        for en in ("zlib", "shuffle", "complevel"):
            if en in dataset[cvar].encoding:
                del dataset[cvar].encoding[en]
                changed = True

    for var in dataset.data_vars:
        complevel = dataset[var].encoding.get("complevel", 0)
        if isinstance(complevel, (int, float)) and complevel > 1:
            dataset[var].encoding["complevel"] = 1
            dataset[var].encoding["zlib"] = True
            dataset[var].encoding["shuffle"] = True
            changed = True

    return changed


def apply_atlas_project_id(dataset: xr.Dataset) -> bool:
    project_id = atlas_project_id(dataset)
    if not project_id:
        return False
    if dataset.attrs.get("project_id") == project_id:
        return False
    dataset.attrs["project_id"] = project_id
    return True
