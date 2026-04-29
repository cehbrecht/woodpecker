from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .broken import apply_metadata_corruption
from .factory import dataset_with_attrs, variable_units


def make_cordex(
    variable: str = "tasmax",
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
    seed: int | None = None,
) -> xr.Dataset:
    """Create a small synthetic CORDEX-like regional climate dataset.

    Examples
    --------
    >>> from woodpecker.testing import make_cordex
    >>> ds = make_cordex()
    >>> ds.attrs["project_id"]
    'CORDEX'
    >>> "tasmax" in ds
    True
    """
    attrs = _cordex_attrs(variable)
    dataset = dataset_with_attrs(variable, attrs=attrs, seed=seed)
    return apply_metadata_corruption(
        dataset,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
    )


def _cordex_attrs(variable: str) -> dict[str, str]:
    dataset_id = (
        f"CORDEX.output.EUR-11.SMHI.MOHC-HadGEM2-ES.rcp85.r1i1p1."
        f"RCA4.v1.day.{variable}.v20200101"
    )
    return {
        "project_id": "CORDEX",
        "dataset_id": dataset_id,
        "source_name": f"{dataset_id}.nc",
        "domain_id": "EUR-11",
        "driving_model_id": "MOHC-HadGEM2-ES",
        "driving_experiment_id": "rcp85",
        "driving_model_ensemble_member": "r1i1p1",
        "rcm_model_id": "RCA4",
        "rcm_version_id": "v1",
        "activity_id": "CORDEX",
        "experiment_id": "rcp85",
        "scenario_id": "rcp85",
        "variable_id": variable,
        "table_id": "day",
        "units": variable_units(variable),
        "frequency": "day",
        "grid_label": "EUR-11",
    }
