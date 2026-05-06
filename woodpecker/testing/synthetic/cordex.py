from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .factory import make_dataset, variable_units


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
    return make_dataset(
        variable=variable,
        attrs_factory=_cordex_attrs,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
        seed=seed,
    )


def _cordex_attrs(variable: str) -> dict[str, str]:
    dataset_id = (
        f"CORDEX.output.EUR-11.SMHI.MOHC-HadGEM2-ES.rcp85.r1i1p1.RCA4.v1.day.{variable}.v20200101"
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
