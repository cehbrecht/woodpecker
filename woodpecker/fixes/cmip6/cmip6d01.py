from __future__ import annotations

import xarray as xr

from ..registry import Fix, FixRegistry


def _lower_source_name(dataset: xr.Dataset) -> str:
    return str(dataset.attrs.get("source_name", "")).lower()


def _needs_time_long_name_fix(dataset: xr.Dataset) -> bool:
    if "time" not in dataset:
        return False
    return dataset["time"].attrs.get("long_name") != "valid_time"


def _needs_realization_var_fix(dataset: xr.Dataset) -> bool:
    if "realization" in dataset.data_vars:
        return False
    return "realization_index" in dataset.attrs


def _apply_time_long_name_fix(dataset: xr.Dataset) -> bool:
    if not _needs_time_long_name_fix(dataset):
        return False
    dataset["time"].attrs["long_name"] = "valid_time"
    return True


def _apply_realization_var_fix(dataset: xr.Dataset) -> bool:
    if not _needs_realization_var_fix(dataset):
        return False

    raw_value = dataset.attrs.get("realization_index")
    try:
        realization_value = int(raw_value)
    except (TypeError, ValueError):
        return False

    dataset["realization"] = xr.DataArray(realization_value)
    dataset["realization"].attrs["long_name"] = "realization"
    dataset["realization"].attrs[
        "comment"
    ] = "For more information on the ripf, refer to variant_label and global attributes."
    return True


@FixRegistry.register
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal metadata baseline"
    description = "Applies simple CMIP6-decadal metadata fixes inspired by rook utilities."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        source = _lower_source_name(dataset)
        return source.endswith(".nc") and "cmip6" in source

    def check(self, dataset: xr.Dataset) -> list[str]:
        findings = []
        if "decadal" not in _lower_source_name(dataset):
            findings.append("expected CMIP6 decadal filename hint ('decadal') is missing")
        if _needs_time_long_name_fix(dataset):
            findings.append("time coordinate long_name should be 'valid_time'")
        if _needs_realization_var_fix(dataset):
            findings.append("realization variable should be added from realization_index")
        return findings

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        needs_change = _needs_time_long_name_fix(dataset) or _needs_realization_var_fix(dataset)
        if not needs_change:
            return False

        if dry_run:
            return True

        changed = _apply_time_long_name_fix(dataset)
        changed = _apply_realization_var_fix(dataset) or changed
        return changed
