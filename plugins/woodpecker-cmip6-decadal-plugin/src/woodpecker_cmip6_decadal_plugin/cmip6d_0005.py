from __future__ import annotations

import xarray as xr

from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import is_cmip6_decadal_netcdf

EXPECTED_REALIZATION_COMMENT = (
    "For more information on the ripf, refer to the variant_label, "
    "initialization_description, physics_description and forcing_description "
    "global attributes"
)


def _needs_realization_comment_fix(dataset: xr.Dataset) -> bool:
    if "realization" not in dataset.data_vars:
        return False
    return dataset["realization"].attrs.get("comment") != EXPECTED_REALIZATION_COMMENT


def _apply_realization_comment_fix(dataset: xr.Dataset) -> bool:
    if not _needs_realization_comment_fix(dataset):
        return False
    dataset["realization"].attrs["comment"] = EXPECTED_REALIZATION_COMMENT
    return True


@FixRegistry.register
class DecadalRealizationCommentNormalizationFix(Fix):
    local_id = "0005"
    name = "Decadal realization comment normalization"
    description = "Normalizes realization comment to the full CMIP6-decadal ripf guidance text."
    categories = ["metadata"]
    priority = 14
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_realization_comment_fix(dataset):
            return ["realization comment should be normalized to CMIP6-decadal ripf guidance"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_realization_comment_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_realization_comment_fix(dataset)
