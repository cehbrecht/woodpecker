"""End-to-end public API examples for CMIP7 fix plans."""

import numpy as np
import pytest

from woodpecker.testing import make_cmip7

from .helpers import assert_plan_check_fix_cycle, example_plan_path

pytest.importorskip("woodpecker_cmip7_plugin")

ESA_CCI_SOURCE_NAME = "ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"


def _esa_cci_water_vapour_dataset():
    dataset = make_cmip7(
        variable="prw",
        overrides={"source_name": ESA_CCI_SOURCE_NAME},
        seed=7,
    )
    dataset = dataset.isel(lat=slice(None, None, -1))
    dataset = dataset.assign_coords(bnds=[0, 1])
    dataset["lat_bnds"] = (
        ("lat", "bnds"),
        np.column_stack([dataset["lat"].values - 0.5, dataset["lat"].values + 0.5]),
    )
    return dataset


def test_esa_cci_zarr_plan_checks_and_fixes_synthetic_cmip7_dataset():
    dataset = _esa_cci_water_vapour_dataset()
    plan_path = example_plan_path("esa_cci_water_vapour_plan.json")

    def assert_unchanged(ds):
        assert "prw" in ds.data_vars
        assert "bnds" in ds.dims
        assert float(ds["lat"].values[0]) > float(ds["lat"].values[-1])

    def assert_fixed(ds):
        assert "tcwv" in ds.data_vars
        assert "prw" not in ds.data_vars
        assert "nv" in ds.dims
        assert "bnds" not in ds.dims
        assert ds.attrs["realm"] == "atmos"
        assert ds.attrs["branded_variable"] == "prw_tavg-u-hxy-u"
        assert float(ds["lat"].values[0]) < float(ds["lat"].values[-1])

    assert_plan_check_fix_cycle(
        plan_path,
        dataset,
        expected_fix_ids=(
            "cmip7.configurable_reformat_bridge",
            "woodpecker.ensure_latitude_is_increasing",
        ),
        expected_changed=2,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
