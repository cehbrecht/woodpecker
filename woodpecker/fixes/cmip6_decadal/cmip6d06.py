from __future__ import annotations

import numpy as np
import xarray as xr

from ..registry import Fix, FixRegistry
from .common import is_cmip6_decadal_netcdf


def _needs_realization_dtype_fix(dataset: xr.Dataset) -> bool:
    if "realization" not in dataset.data_vars:
        return False
    return dataset["realization"].dtype != np.int32


def _apply_realization_dtype_fix(dataset: xr.Dataset) -> bool:
    if not _needs_realization_dtype_fix(dataset):
        return False

    realization = dataset["realization"].astype(np.int32)
    realization.attrs = dict(dataset["realization"].attrs)
    realization.encoding = dict(dataset["realization"].encoding)
    dataset["realization"] = realization
    return True


@FixRegistry.register
class CMIP6D06(Fix):
    code = "CMIP6D06"
    name = "Decadal realization dtype normalization"
    description = "Normalizes realization data variable dtype to int32 for CMIP6-decadal datasets."
    categories = ["metadata", "structure"]
    priority = 15
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_realization_dtype_fix(dataset):
            return ["realization dtype should be normalized to int32"]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_realization_dtype_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_realization_dtype_fix(dataset)