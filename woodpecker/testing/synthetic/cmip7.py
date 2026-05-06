from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .factory import make_dataset, variable_units


def make_cmip7(
    variable: str = "tas",
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
    seed: int | None = None,
) -> xr.Dataset:
    """Create a small synthetic CMIP7-like dataset.

    Examples
    --------
    >>> from woodpecker.testing import make_cmip7
    >>> ds = make_cmip7()
    >>> ds.attrs["project_id"]
    'CMIP7'
    >>> broken = make_cmip7(missing=["project_id"], rename_vars={"tas": "temp"})
    >>> "project_id" in broken.attrs
    False
    """
    return make_dataset(
        variable=variable,
        attrs_factory=_cmip7_attrs,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
        seed=seed,
    )


def _cmip7_attrs(variable: str) -> dict[str, str]:
    dataset_id = f"CMIP7.CMIP.MOHC.UKESM2-1.historical.r1i1p1f1.Amon.{variable}.gn.v20260101"
    return {
        "project_id": "CMIP7",
        "dataset_id": dataset_id,
        "source_file": f"{dataset_id}.nc",
        "source_id": "UKESM2-1",
        "source_name": "UKESM2-1",
        "mip_era": "CMIP7",
        "activity_id": "CMIP",
        "experiment_id": "historical",
        "variant_label": "r1i1p1f1",
        "variable_id": variable,
        "table_id": "Amon",
        "units": variable_units(variable),
        "frequency": "mon",
        "grid_label": "gn",
        "nominal_resolution": "100 km",
    }
