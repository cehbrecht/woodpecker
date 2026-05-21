import numpy as np
import woodpecker_xmip_plugin  # noqa: F401
import xarray as xr
from _xmip_helpers import assert_check_fix_cycle

from woodpecker.fixes.registry import FixRegistry

EXPECTED_FIX_IDS = {
    "xmip.cmip6_preprocessing",
}


def _raw_cmip6_dataset() -> xr.Dataset:
    x = np.array([-10.0, 0.0, 10.0])
    y = np.array([-1.0, 1.0])
    longitude = xr.DataArray(
        np.array([[-10.0, 0.0, 10.0], [-10.0, 0.0, 10.0]]),
        dims=("j", "i"),
    )
    latitude = xr.DataArray(
        np.array([[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]]),
        dims=("j", "i"),
    )
    dataset = xr.Dataset(
        data_vars={
            "tas": (("j", "i"), np.ones((2, 3))),
            "longitude": longitude,
            "latitude": latitude,
        },
        coords={"i": x, "j": y},
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
    return dataset


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = _raw_cmip6_dataset()
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids) == EXPECTED_FIX_IDS


def test_xmip_cmip6_preprocessing_is_detected_and_applied():
    dataset = _raw_cmip6_dataset()

    def assert_unchanged(ds):
        assert "i" in ds.dims
        assert "j" in ds.dims
        assert "longitude" in ds.data_vars
        assert "latitude" in ds.data_vars
        assert float(ds["longitude"].min()) < 0

    def assert_fixed(ds):
        assert "x" in ds.dims
        assert "y" in ds.dims
        assert "lon" in ds.coords
        assert "lat" in ds.coords
        assert "longitude" not in ds.variables
        assert "latitude" not in ds.variables
        assert float(ds["lon"].min()) >= 0
        assert ds.attrs["branch_time_in_parent"] == 91250

    assert_check_fix_cycle(
        dataset,
        "xmip.cmip6_preprocessing",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_xmip_cmip6_preprocessing_ignores_non_cmip6():
    dataset = _raw_cmip6_dataset()
    dataset.attrs["project_id"] = "CMIP5"
    dataset.attrs["mip_era"] = "CMIP5"

    fix = woodpecker_xmip_plugin.XmipCmip6PreprocessingFix()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []
    assert fix.apply(dataset, dry_run=False) is False


def test_xmip_combined_preprocessing_alias_resolves():
    assert FixRegistry.resolve_identifier("xmip.combined_preprocessing") == (
        "xmip.cmip6_preprocessing"
    )
