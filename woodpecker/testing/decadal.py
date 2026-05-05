from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .factory import make_dataset, variable_units


def make_cmip6_decadal(
    variable: str = "tos",
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
    seed: int | None = None,
) -> xr.Dataset:
    """Create a small synthetic CMIP6 decadal prediction dataset.

    Examples
    --------
    >>> from woodpecker.testing import make_cmip6_decadal
    >>> ds = make_cmip6_decadal()
    >>> ds.attrs["activity_id"]
    'DCPP'
    >>> broken = make_cmip6_decadal(missing=["sub_experiment_id"])
    >>> "sub_experiment_id" in broken.attrs
    False
    """
    return make_dataset(
        variable=variable,
        attrs_factory=_cmip6_decadal_attrs,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
        seed=seed,
    )


def _cmip6_decadal_attrs(variable: str) -> dict[str, str]:
    dataset_id = (
        f"CMIP6.DCPP.MPI-M.MPI-ESM1-2-HR.dcppA-hindcast.s1960-r1i1p1f1.Omon.{variable}.gn.v20200101"
    )
    return {
        "project_id": "CMIP6",
        "dataset_id": dataset_id,
        "source_file": f"{dataset_id}.nc",
        "source_id": "MPI-ESM1-2-HR",
        "source_name": "MPI-ESM1-2-HR",
        "mip_era": "CMIP6",
        "activity_id": "DCPP",
        "experiment_id": "dcppA-hindcast",
        "sub_experiment_id": "s1960",
        "variant_label": "r1i1p1f1",
        "variable_id": variable,
        "table_id": "Omon",
        "units": variable_units(variable),
        "frequency": "mon",
        "grid_label": "gn",
        "nominal_resolution": "100 km",
    }
