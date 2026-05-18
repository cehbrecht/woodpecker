from pathlib import Path

import numpy as np
import woodpecker_cmip7_plugin  # noqa: F401
from _cmip7_helpers import assert_check_fix_cycle, assert_plan_check_fix_cycle

from woodpecker.fixes.registry import FixRegistry
from woodpecker.testing import make_cmip7

EXPECTED_FIX_IDS = {
    "cmip7.configurable_reformat_bridge",
    "cmip7.ensure_project_id_present",
    "cmip7.rename_temp_variable_to_tas",
}
ESA_CCI_SOURCE_NAME = "ESACCI-WATERVAPOUR-L3C-TCWV-meris-005deg-2002-2017-fv3.2.zarr"
PLAN_PATH = Path(__file__).parent / "plans" / "esa_cci_water_vapour_plan.json"


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_cmip7(missing=["project_id"], rename_vars={"tas": "temp"})
    findings = woodpecker.check(
        dataset,
        fixes=[
            "cmip7.ensure_project_id_present",
            "cmip7.rename_temp_variable_to_tas",
        ],
    )

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)


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


def test_cmip7_missing_project_id_is_detected_and_fixed():
    dataset = make_cmip7(missing=["project_id"])

    def assert_fixed(ds):
        assert ds.attrs["project_id"] == "CMIP7"

    assert_check_fix_cycle(
        dataset,
        "cmip7.ensure_project_id_present",
        assert_fixed=assert_fixed,
    )


def test_cmip7_temp_variable_is_detected_and_renamed_to_tas():
    dataset = make_cmip7(rename_vars={"tas": "temp"})

    def assert_unchanged(ds):
        assert set(ds.data_vars) == {"temp"}

    def assert_fixed(ds):
        assert set(ds.data_vars) == {"tas"}

    assert_check_fix_cycle(
        dataset,
        "cmip7.rename_temp_variable_to_tas",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_esa_cci_zarr_plan_checks_and_fixes_synthetic_cmip7_dataset():
    dataset = _esa_cci_water_vapour_dataset()

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
        PLAN_PATH,
        dataset,
        expected_fix_ids=(
            "cmip7.configurable_reformat_bridge",
            "woodpecker.ensure_latitude_is_increasing",
        ),
        expected_changed=2,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
