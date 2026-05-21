from pathlib import Path

import numpy as np
import woodpecker_xmip_plugin  # noqa: F401
import xarray as xr
from _xmip_helpers import assert_check_fix_cycle

from woodpecker.fixes.registry import FixRegistry

EXPECTED_FIX_IDS = {
    "xmip.broadcast_lon_lat",
    "xmip.convert_bounds_to_vertices",
    "xmip.convert_vertices_to_bounds",
    "xmip.drop_helper_grid_coords",
    "xmip.fix_known_cmip6_metadata",
    "xmip.mark_spatial_coords",
    "xmip.normalize_lon_lat_bounds",
    "xmip.normalize_longitude_convention",
    "xmip.promote_missing_dimension_coords",
    "xmip.rename_cmip6_axes",
    "xmip.sort_vertex_order",
}
PLAN_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "woodpecker_xmip_plugin"
    / "plans"
    / "cmip6_preprocessing.yaml"
)


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
    return xr.Dataset(
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


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = _raw_cmip6_dataset()
    findings = woodpecker.check(
        dataset,
        fixes=[
            "xmip.rename_cmip6_axes",
            "xmip.fix_known_cmip6_metadata",
        ],
    )

    assert findings
    assert set(findings.fix_ids) == {
        "xmip.rename_cmip6_axes",
        "xmip.fix_known_cmip6_metadata",
    }


def test_xmip_rename_cmip6_axes_is_detected_and_applied():
    dataset = _raw_cmip6_dataset()

    def assert_unchanged(ds):
        assert "i" in ds.dims
        assert "j" in ds.dims
        assert "longitude" in ds.data_vars
        assert "latitude" in ds.data_vars

    def assert_fixed(ds):
        assert "x" in ds.dims
        assert "y" in ds.dims
        assert "lon" in ds.data_vars
        assert "lat" in ds.data_vars
        assert "longitude" not in ds.variables
        assert "latitude" not in ds.variables

    assert_check_fix_cycle(
        dataset,
        "xmip.rename_cmip6_axes",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_xmip_mark_spatial_coords_is_detected_and_applied_after_rename():
    dataset = _raw_cmip6_dataset()
    woodpecker_xmip_plugin.RenameCmip6AxesFix().apply(dataset, dry_run=False)

    def assert_fixed(ds):
        assert "lon" in ds.coords
        assert "lat" in ds.coords

    assert_check_fix_cycle(
        dataset,
        "xmip.mark_spatial_coords",
        assert_fixed=assert_fixed,
    )


def test_xmip_normalize_longitude_convention_is_detected_and_applied_after_rename():
    dataset = _raw_cmip6_dataset()
    woodpecker_xmip_plugin.RenameCmip6AxesFix().apply(dataset, dry_run=False)
    woodpecker_xmip_plugin.MarkSpatialCoordsFix().apply(dataset, dry_run=False)

    def assert_fixed(ds):
        assert float(ds["lon"].min()) >= 0

    assert_check_fix_cycle(
        dataset,
        "xmip.normalize_longitude_convention",
        assert_fixed=assert_fixed,
    )


def test_xmip_metadata_fix_ignores_non_cmip6():
    dataset = _raw_cmip6_dataset()
    dataset.attrs["project_id"] = "CMIP5"
    dataset.attrs["mip_era"] = "CMIP5"

    fix = woodpecker_xmip_plugin.FixKnownCmip6MetadataFix()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []
    assert fix.apply(dataset, dry_run=False) is False


def test_xmip_cmip6_preprocessing_plan_checks_and_fixes_dataset():
    import woodpecker

    dataset = _raw_cmip6_dataset()

    findings = woodpecker.plan.check(dataset, PLAN_PATH)
    assert set(findings.fix_ids) == {
        "xmip.rename_cmip6_axes",
        "xmip.fix_known_cmip6_metadata",
    }

    preview = woodpecker.plan.fix(dataset, PLAN_PATH, dry_run=True)
    assert preview.changed == 2
    assert "i" in dataset.dims
    assert "branch_time_in_parent" not in dataset.attrs

    write = woodpecker.plan.fix(dataset, PLAN_PATH, dry_run=False)
    assert write.changed == 4
    assert "x" in dataset.dims
    assert "y" in dataset.dims
    assert "lon" in dataset.coords
    assert "lat" in dataset.coords
    assert float(dataset["lon"].min()) >= 0
    assert dataset.attrs["branch_time_in_parent"] == 91250
    assert not woodpecker.plan.check(dataset, PLAN_PATH)
