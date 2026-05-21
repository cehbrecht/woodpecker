"""End-to-end public API examples for xMIP-derived plugin plans."""

from importlib.resources import as_file, files

import numpy as np
import pytest
import xarray as xr

import woodpecker

pytest.importorskip("woodpecker_xmip_plugin")

from .helpers import unique_in_order  # noqa: E402


def _xmip_plan_path():
    plan_ref = files("woodpecker_xmip_plugin") / "plans" / "cmip6_preprocessing.yaml"
    return as_file(plan_ref)


def _raw_cmip6_grid_dataset() -> xr.Dataset:
    longitude = xr.DataArray(
        np.array([[-10.0, 0.0, 10.0], [-10.0, 0.0, 10.0]]),
        dims=("j", "i"),
    )
    latitude = xr.DataArray(
        np.array([[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]]),
        dims=("j", "i"),
    )
    return xr.Dataset(
        data_vars={
            "tas": (("j", "i", "lev"), np.ones((2, 3, 2))),
            "longitude": longitude,
            "latitude": latitude,
        },
        coords={
            "i": [-10.0, 0.0, 10.0],
            "j": [-1.0, 1.0],
            "lev": ("lev", [0.0, 100.0], {"units": "centimeters"}),
        },
        attrs={
            "project_id": "CMIP6",
            "source_id": "GFDL-CM4",
            "experiment_id": "historical",
            "variable_id": "tas",
            "table_id": "Amon",
            "grid_label": "gn",
            "variant_label": "r1i1p1f1",
        },
    )


def test_xmip_cmip6_preprocessing_plan_checks_and_fixes_synthetic_dataset():
    dataset = _raw_cmip6_grid_dataset()

    with _xmip_plan_path() as plan_path:
        findings = woodpecker.plan.check(
            dataset,
            plan_path,
            plan_id="xmip.cmip6_preprocessing",
        )

        assert unique_in_order(findings.fix_ids) == (
            "xmip.rename_cmip6_axes",
            "xmip.normalize_coordinate_units",
            "xmip.fix_known_cmip6_metadata",
        )

        preview = woodpecker.plan.fix(
            dataset,
            plan_path,
            plan_id="xmip.cmip6_preprocessing",
            dry_run=True,
        )
        assert preview.changed == 3
        assert "i" in dataset.dims
        assert "longitude" in dataset.data_vars
        assert dataset["lev"].attrs["units"] == "centimeters"
        assert "branch_time_in_parent" not in dataset.attrs

        write = woodpecker.plan.fix(
            dataset,
            plan_path,
            plan_id="xmip.cmip6_preprocessing",
            dry_run=False,
        )

        assert write.changed == 5
        assert write.persisted == 1
        assert "x" in dataset.dims
        assert "y" in dataset.dims
        assert "lon" in dataset.coords
        assert "lat" in dataset.coords
        assert "longitude" not in dataset.variables
        assert "latitude" not in dataset.variables
        assert float(dataset["lon"].min()) >= 0
        np.testing.assert_allclose(dataset["lev"].values, [0.0, 1.0])
        assert dataset["lev"].attrs["units"] == "m"
        assert dataset.attrs["branch_time_in_parent"] == 91250

        assert not woodpecker.plan.check(
            dataset,
            plan_path,
            plan_id="xmip.cmip6_preprocessing",
        )
