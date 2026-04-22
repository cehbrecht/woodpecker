from __future__ import annotations

import xarray as xr

from woodpecker.fixes.common.helpers import lower_source_name
from woodpecker.fixes.registry import Fix, FixRegistry

from .helpers import is_cmip6_decadal_netcdf

MODEL_SPECIFIC_GLOBAL_ATTRS: dict[str, dict[str, str]] = {
    "cmcc-cm2-sr5": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",
        "initialization_description": "hindcast initialized based on observations and using historical forcing",
    },
    "ec-earth3": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",
        "initialization_description": "Atmosphere initialization based on full-fields from ERA-Interim (s1979-s2018) or ERA-40 (s1960-s1978); ocean/sea-ice initialization based on full-fields from NEMO/LIM assimilation run nudged towards ORA-S4 (s1960-s2018)",
    },
    "hadgem3-gc31-mm": {
        "forcing_description": "f2, CMIP6 v6.2.0 forcings; no ozone remapping",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",
        "initialization_description": "hindcast initialized based on observations and using historical forcing",
    },
    "mpi-esm1-2-hr": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",
        "initialization_description": "hindcast initialized based on observations and using historical forcing",
    },
    "mpi-esm1-2-lr": {
        "forcing_description": "f1, CMIP6 historical forcings",
        "physics_description": "physics from the standard model configuration, with no additional tuning or different parametrization",
        "initialization_description": "hindcast initialized based on observations and using historical forcing",
    },
}


def _model_attrs_for_dataset(dataset: xr.Dataset) -> dict[str, str] | None:
    source = lower_source_name(dataset)
    for model, attrs in MODEL_SPECIFIC_GLOBAL_ATTRS.items():
        if model in source:
            return attrs
    return None


def _needs_model_global_attrs_fix(dataset: xr.Dataset) -> bool:
    expected = _model_attrs_for_dataset(dataset)
    if not expected:
        return False
    return any(dataset.attrs.get(key) != value for key, value in expected.items())


def _apply_model_global_attrs_fix(dataset: xr.Dataset) -> bool:
    expected = _model_attrs_for_dataset(dataset)
    if not expected:
        return False
    changed = False
    for key, value in expected.items():
        if dataset.attrs.get(key) != value:
            dataset.attrs[key] = value
            changed = True
    return changed


@FixRegistry.register
class DecadalModelGlobalAttributesFix(Fix):
    local_id = "model_global_attributes"
    name = "Decadal model global attributes"
    description = "Normalizes model-specific global metadata fields for CMIP6-decadal datasets."
    categories = ["metadata"]
    priority = 22
    dataset = "CMIP6-decadal"

    def matches(self, dataset: xr.Dataset) -> bool:
        return is_cmip6_decadal_netcdf(dataset)

    def check(self, dataset: xr.Dataset) -> list[str]:
        if not is_cmip6_decadal_netcdf(dataset):
            return []
        if _needs_model_global_attrs_fix(dataset):
            return [
                "model-specific forcing/physics/initialization global attributes should be normalized"
            ]
        return []

    def apply(self, dataset: xr.Dataset, dry_run: bool = True) -> bool:
        if not is_cmip6_decadal_netcdf(dataset):
            return False
        if not _needs_model_global_attrs_fix(dataset):
            return False
        if dry_run:
            return True
        return _apply_model_global_attrs_fix(dataset)
