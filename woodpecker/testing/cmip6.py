from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .factory import make_dataset, variable_units


def make_cmip6(
    variable: str = "tas",
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
    seed: int | None = None,
) -> xr.Dataset:
    """Create a small synthetic CMIP6-like dataset.

    The default output has monthly ``time`` plus regular ``lat``/``lon`` axes,
    realistic CMIP6 identity metadata, and deterministic values.

    Examples
    --------
    >>> from woodpecker.testing import make_cmip6
    >>> ds = make_cmip6()
    >>> ds.dims["time"]
    12
    >>> broken = make_cmip6(missing=["units"], rename_vars={"tas": "temperature"})
    >>> "units" in broken.attrs
    False
    """
    return make_dataset(
        variable=variable,
        attrs_factory=_cmip6_attrs,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
        seed=seed,
    )


def _cmip6_attrs(variable: str) -> dict[str, str]:
    dataset_id = f"CMIP6.CMIP.MOHC.HadGEM3-GC31-LL.historical.r1i1p1f3.Amon.{variable}.gn.v20200101"
    return {
        "project_id": "CMIP6",
        "dataset_id": dataset_id,
        "source_file": f"{dataset_id}.nc",
        "source_id": "HadGEM3-GC31-LL",
        "source_name": "HadGEM3-GC31-LL",
        "mip_era": "CMIP6",
        "activity_id": "CMIP",
        "experiment_id": "historical",
        "variant_label": "r1i1p1f3",
        "variable_id": variable,
        "table_id": "Amon",
        "units": variable_units(variable),
        "frequency": "mon",
        "grid_label": "gn",
        "nominal_resolution": "250 km",
    }
