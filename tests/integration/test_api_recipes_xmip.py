"""End-to-end public API examples for xMIP-derived plugin recipes."""

import numpy as np
import pytest

import woodpecker
from woodpecker.testing import make_cmip6

pytest.importorskip("woodpecker_xmip_plugin")

from .helpers import unique_in_order  # noqa: E402


def _xmip_corrupted_cmip6_dataset():
    dataset = make_cmip6(
        overrides={
            "source_id": "GFDL-CM4",
            "experiment_id": "historical",
        },
        seed=7,
    )
    dataset = dataset.isel(time=slice(0, 2), lat=slice(0, 2), lon=slice(0, 3))
    dataset = dataset.rename({"lat": "j", "lon": "i"})
    dataset = dataset.expand_dims({"lev": [0.0, 100.0]})
    dataset["lev"].attrs["units"] = "centimeters"

    longitude = np.broadcast_to(np.array([-10.0, 0.0, 10.0]), (dataset.sizes["j"], 3))
    latitude = np.broadcast_to(
        np.asarray(dataset["j"].values)[:, None],
        (dataset.sizes["j"], dataset.sizes["i"]),
    )
    dataset["longitude"] = (("j", "i"), longitude)
    dataset["latitude"] = (("j", "i"), latitude)
    return dataset


def test_xmip_cmip6_preprocessing_plan_checks_and_fixes_synthetic_dataset():
    dataset = _xmip_corrupted_cmip6_dataset()

    recipe = woodpecker.recipe.get("xmip.cmip6_preprocessing")
    findings = woodpecker.recipe.check(dataset, recipe)

    assert unique_in_order(findings.fix_ids) == (
        "woodpecker.rename_variables",
        "woodpecker.convert_units",
        "xmip.fix_known_cmip6_metadata",
    )

    preview = woodpecker.recipe.fix(dataset, recipe, dry_run=True)
    assert preview.changed == 3
    assert "i" in dataset.dims
    assert "longitude" in dataset.data_vars
    assert dataset["lev"].attrs["units"] == "centimeters"
    assert "branch_time_in_parent" not in dataset.attrs

    write = woodpecker.recipe.fix(dataset, recipe, dry_run=False)

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

    assert not woodpecker.recipe.check(dataset, recipe)
