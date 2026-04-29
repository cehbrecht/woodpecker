from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import xarray as xr

from .broken import apply_metadata_corruption
from .factory import dataset_with_attrs, variable_units


def make_atlas(
    variable: str = "pr",
    *,
    missing: Iterable[str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    rename_vars: Mapping[str, str] | None = None,
    seed: int | None = None,
) -> xr.Dataset:
    """Create a small synthetic C3S Atlas-like dataset.

    Examples
    --------
    >>> from woodpecker.testing import make_atlas
    >>> ds = make_atlas()
    >>> ds.attrs["project_id"]
    'C3S-Atlas'
    >>> broken = make_atlas(overrides={"units": "mm day-1"})
    >>> broken["pr"].attrs["units"]
    'mm day-1'
    """
    attrs = _atlas_attrs(variable)
    dataset = dataset_with_attrs(variable, attrs=attrs, seed=seed)
    return apply_metadata_corruption(
        dataset,
        missing=missing,
        overrides=overrides,
        rename_vars=rename_vars,
    )


def _atlas_attrs(variable: str) -> dict[str, str]:
    dataset_id = f"c3s-ipcc-atlas.cmip6.historical.ssp245.{variable}.monthly.global"
    return {
        "project_id": "C3S-Atlas",
        "dataset_id": dataset_id,
        "ds_id": dataset_id,
        "source_name": f"{dataset_id}.nc",
        "experiment_id": "ssp245",
        "variable_id": variable,
        "table_id": "Amon",
        "units": variable_units(variable),
        "frequency": "mon",
        "grid_label": "gr",
        "atlas_region": "global",
    }
