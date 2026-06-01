"""xMIP plugin tests.

The parity-style tests below adapt cases from xMIP's preprocessing tests while
running them through Woodpecker fix functions and plans:
https://github.com/jbusecke/xMIP/blob/main/tests/test_preprocessing.py

The corresponding original implementation lives in:
https://github.com/jbusecke/xMIP/blob/main/xmip/preprocessing.py
"""

import itertools

import numpy as np
import woodpecker_xmip_plugin  # noqa: F401
import xarray as xr
from _xmip_helpers import assert_check_fix_cycle

import woodpecker
from woodpecker.fixes.registry import FixFunctionRegistry
from woodpecker.testing import make_cmip6

EXPECTED_FIX_IDS = {
    "xmip.broadcast_lon_lat",
    "xmip.convert_bounds_to_vertices",
    "xmip.convert_vertices_to_bounds",
    "xmip.drop_helper_grid_coords",
    "xmip.fix_known_cmip6_metadata",
    "xmip.mark_spatial_coords",
    "xmip.normalize_coordinate_units",
    "xmip.normalize_lon_lat_bounds",
    "xmip.replace_xy_with_nominal_lon_lat",
    "xmip.rename_cmip6_axes",
    "xmip.sort_vertex_order",
}
PLAN = woodpecker.plan.get("xmip.cmip6_preprocessing")


def _raw_cmip6_dataset() -> xr.Dataset:
    dataset = make_cmip6(
        overrides={
            "source_id": "GFDL-CM4",
            "source_name": "GFDL-CM4",
            "experiment_id": "historical",
            "variant_label": "r1i1p1f1",
        },
        periods=1,
        nlat=2,
        nlon=3,
        seed=1,
    )
    dataset = dataset.isel(time=0, drop=True).rename({"lat": "j", "lon": "i"})
    dataset = dataset.assign_coords(i=np.array([-10.0, 0.0, 10.0]), j=np.array([-1.0, 1.0]))
    dataset["longitude"] = (("j", "i"), np.broadcast_to(dataset.i.values, (2, 3)))
    dataset["latitude"] = (("j", "i"), np.broadcast_to(dataset.j.values[:, None], (2, 3)))
    return dataset


def _xy_dataset_with_2d_lon_lat(*, nlat: int = 10, nlon: int = 10) -> xr.Dataset:
    dataset = make_cmip6(periods=1, nlat=nlat, nlon=nlon, seed=2)
    dataset = dataset.isel(time=0, drop=True).rename({"lat": "y", "lon": "x"})
    dataset = dataset.assign_coords(x=np.arange(nlon), y=np.arange(20, 20 + nlat))
    dataset.coords["lon"] = dataset.x * xr.ones_like(dataset.y)
    dataset.coords["lat"] = xr.ones_like(dataset.x) * dataset.y
    return dataset


def _dataset_with_bounds() -> xr.Dataset:
    dataset = _xy_dataset_with_2d_lon_lat()
    for variable in ("lon", "lat"):
        dataset.coords[f"{variable}_bounds"] = dataset[variable] + xr.DataArray(
            [-0.01, 0.01],
            dims=("bnds",),
        )
    return dataset


def _dataset_with_vertices(order: tuple[int, int, int, int] = (0, 1, 2, 3)) -> xr.Dataset:
    ordered_lon_lat = np.array([[1, 1], [1, 4], [2, 4], [2, 1]])
    scrambled = ordered_lon_lat[list(order), :]

    dataset = _xy_dataset_with_2d_lon_lat(nlat=1, nlon=1)
    dataset.coords["lon_verticies"] = xr.DataArray(
        scrambled[:, 0],
        dims=("vertex",),
    ).expand_dims(x=dataset.x, y=dataset.y)
    dataset.coords["lat_verticies"] = xr.DataArray(
        scrambled[:, 1],
        dims=("vertex",),
    ).expand_dims(x=dataset.x, y=dataset.y)
    return dataset


def _assert_vertices_match_rectangular_bounds(dataset: xr.Dataset) -> None:
    lon_bounds = xr.ones_like(dataset.lat) * dataset.coords["lon_bounds"]
    lat_bounds = xr.ones_like(dataset.lon) * dataset.coords["lat_bounds"]

    lon_vertices = xr.concat(
        [lon_bounds.isel(bnds=index).squeeze(drop=True) for index in (0, 0, 1, 1)],
        dim="vertex",
    ).reset_coords(drop=True)
    lat_vertices = xr.concat(
        [lat_bounds.isel(bnds=index).squeeze(drop=True) for index in (0, 1, 1, 0)],
        dim="vertex",
    ).reset_coords(drop=True)

    assert dataset.lon_verticies.dims == lon_vertices.dims
    assert dataset.lat_verticies.dims == lat_vertices.dims
    np.testing.assert_allclose(dataset.lon_verticies.data, lon_vertices.data)
    np.testing.assert_allclose(dataset.lat_verticies.data, lat_vertices.data)


def _assert_bounds_match_rectangular_vertices(dataset: xr.Dataset) -> None:
    expected_lon_bounds = xr.concat(
        [
            dataset["lon_verticies"].isel(vertex=[0, 1]).mean("vertex"),
            dataset["lon_verticies"].isel(vertex=[2, 3]).mean("vertex"),
        ],
        dim="bnds",
    )
    expected_lat_bounds = xr.concat(
        [
            dataset["lat_verticies"].isel(vertex=[0, 3]).mean("vertex"),
            dataset["lat_verticies"].isel(vertex=[1, 2]).mean("vertex"),
        ],
        dim="bnds",
    )

    assert dataset.lon_bounds.dims == expected_lon_bounds.dims
    assert dataset.lat_bounds.dims == expected_lat_bounds.dims
    np.testing.assert_allclose(dataset.lon_bounds.data, expected_lon_bounds.data)
    np.testing.assert_allclose(dataset.lat_bounds.data, expected_lat_bounds.data)


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixFunctionRegistry.discover()}

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
    """Adapted from xMIP's ``test_rename_cmip6``."""
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
    woodpecker_xmip_plugin.RenameCmip6Axes().apply(dataset, dry_run=False)

    def assert_fixed(ds):
        assert "lon" in ds.coords
        assert "lat" in ds.coords

    assert_check_fix_cycle(
        dataset,
        "xmip.mark_spatial_coords",
        assert_fixed=assert_fixed,
    )


def test_xmip_broadcast_lon_lat_is_detected_and_applied():
    """Adapted from xMIP's ``test_broadcast_lonlat``."""
    dataset = make_cmip6(periods=1, nlat=30, nlon=72, seed=3)
    dataset = dataset.isel(time=0, drop=True).rename({"lat": "y", "lon": "x"})
    dataset = dataset.assign_coords(
        x=np.arange(-180, 180, 5)[: dataset.sizes["x"]],
        y=np.arange(-90, 90, 6)[: dataset.sizes["y"]],
    )

    def assert_fixed(ds):
        expected_lon = ds.x * xr.ones_like(ds.y)
        expected_lat = xr.ones_like(ds.x) * ds.y

        assert "lon" in ds.coords
        assert "lat" in ds.coords
        assert ds.lon.dims == expected_lon.dims
        assert ds.lat.dims == expected_lat.dims
        np.testing.assert_allclose(ds.lon.data, expected_lon.data)
        np.testing.assert_allclose(ds.lat.data, expected_lat.data)

    assert_check_fix_cycle(
        dataset,
        "xmip.broadcast_lon_lat",
        assert_fixed=assert_fixed,
    )


def test_xmip_normalize_longitude_convention_is_detected_and_applied_after_rename():
    dataset = _raw_cmip6_dataset()
    woodpecker_xmip_plugin.RenameCmip6Axes().apply(dataset, dry_run=False)
    woodpecker_xmip_plugin.MarkSpatialCoords().apply(dataset, dry_run=False)

    def assert_fixed(ds):
        assert float(ds["lon"].min()) >= 0

    assert_check_fix_cycle(
        dataset,
        "woodpecker.normalize_longitude_convention",
        assert_fixed=assert_fixed,
    )


def test_xmip_normalize_lon_lat_bounds_renames_vertex_bounds_and_drops_time():
    """Adapted from xMIP's ``test_parse_lon_lat_bounds``."""
    dataset = _xy_dataset_with_2d_lon_lat()
    dataset.coords["lon_bounds"] = (
        xr.DataArray([-0.1, -0.1, 0.1, 0.1], dims=("vertex",)) + dataset["lon"]
    )
    dataset.coords["lat_bounds"] = (
        xr.DataArray([-0.1, 0.1, 0.1, -0.1], dims=("vertex",)) + dataset["lat"]
    )
    dataset.coords["lev_bounds"] = xr.DataArray(
        np.ones((2, 3)),
        dims=("time", "bnds"),
    )

    def assert_fixed(ds):
        assert "lon_verticies" in ds.coords
        assert "lat_verticies" in ds.coords
        assert "lon_bounds" not in ds.variables
        assert "lat_bounds" not in ds.variables
        assert "time" not in ds.lev_bounds.dims

    assert_check_fix_cycle(
        dataset,
        "xmip.normalize_lon_lat_bounds",
        assert_fixed=assert_fixed,
    )


def test_xmip_convert_bounds_to_vertices_is_detected_and_applied():
    """Adapted from xMIP's ``test_maybe_convert_bounds_to_vertex``."""
    dataset = _dataset_with_bounds()

    assert_check_fix_cycle(
        dataset,
        "xmip.convert_bounds_to_vertices",
        assert_fixed=_assert_vertices_match_rectangular_bounds,
    )


def test_xmip_convert_vertices_to_bounds_is_detected_and_applied():
    """Adapted from xMIP's ``test_maybe_convert_vertex_to_bounds``."""
    dataset = _dataset_with_vertices()

    assert_check_fix_cycle(
        dataset,
        "xmip.convert_vertices_to_bounds",
        assert_fixed=_assert_bounds_match_rectangular_vertices,
    )


def test_xmip_sort_vertex_order_matches_upstream_permutations():
    """Adapted from xMIP's ``test_sort_vertex_order``."""
    expected_points = np.array([[1, 1], [1, 4], [2, 4], [2, 1]])

    for order in itertools.permutations(range(4)):
        dataset = _dataset_with_vertices(order)
        changed = woodpecker.fix(
            dataset,
            fixes="xmip.sort_vertex_order",
            dry_run=False,
        ).changed
        assert changed == 1

        sorted_points = np.vstack(
            (
                dataset.lon_verticies.squeeze(drop=True).data,
                dataset.lat_verticies.squeeze(drop=True).data,
            )
        ).T
        np.testing.assert_allclose(sorted_points, expected_points)
        np.testing.assert_allclose(dataset.vertex.data, np.arange(4))
        assert not woodpecker.check(dataset, fixes="xmip.sort_vertex_order")


def test_xmip_drop_helper_grid_coords_is_detected_and_applied():
    dataset = _xy_dataset_with_2d_lon_lat()
    dataset = dataset.assign_coords(bnds=np.arange(2), vertex=np.arange(4))

    def assert_fixed(ds):
        assert "bnds" not in ds.coords
        assert "vertex" not in ds.coords

    assert_check_fix_cycle(
        dataset,
        "xmip.drop_helper_grid_coords",
        assert_fixed=assert_fixed,
    )


def test_xmip_normalize_coordinate_units_is_detected_and_applied():
    """Adapted from xMIP's ``test_correct_units``."""
    dataset = make_cmip6(
        "thetao",
        overrides={"table_id": "Omon"},
        periods=1,
        nlat=1,
        nlon=1,
    )
    dataset = dataset.isel(time=0, lat=0, lon=0, drop=True)
    dataset = dataset.expand_dims(lev=np.array([0.0, 50.0, 100.0]))
    dataset["lev"].attrs["units"] = "centimeters"

    def assert_fixed(ds):
        np.testing.assert_allclose(ds["lev"].values, np.array([0.0, 0.5, 1.0]))
        assert ds["lev"].attrs["units"] == "m"

    assert_check_fix_cycle(
        dataset,
        "xmip.normalize_coordinate_units",
        assert_fixed=assert_fixed,
    )


def test_xmip_replace_xy_with_nominal_lon_lat_is_detected_and_applied():
    """Adapted from xMIP's ``test_replace_x_y_nominal_lat_lon``."""
    x = np.array([0.0, 10.0, 20.0, 30.0])
    y = np.array([-200.0, 0.0, 140.0])
    lon = xr.DataArray(
        np.array(
            [
                [0.0, 50.0, 100.0, 150.0],
                [0.0, 50.0, 100.0, 150.0],
                [0.0, 50.0, 100.0, 150.0],
            ]
        ),
        dims=("y", "x"),
    )
    lat = xr.DataArray(
        np.array(
            [
                [0.0, 0.0, 10.0, 0.0],
                [10.0, 0.0, 0.0, 0.0],
                [20.0, 20.0, 20.0, 20.0],
            ]
        ),
        dims=("y", "x"),
    )
    dataset = make_cmip6(
        "thetao",
        overrides={"table_id": "Omon"},
        periods=1,
        nlat=3,
        nlon=4,
        seed=4,
    )
    dataset = dataset.isel(time=0, drop=True).rename({"lat": "y", "lon": "x"})
    dataset = dataset.assign_coords(x=x, y=y, lon=lon, lat=lat)

    def assert_fixed(ds):
        assert len(ds.x) == len(np.unique(ds.x))
        assert len(ds.y) == len(np.unique(ds.y))
        assert bool((ds.x.diff("x") > 0).all())
        assert bool((ds.y.diff("y") > 0).all())

    assert_check_fix_cycle(
        dataset,
        "xmip.replace_xy_with_nominal_lon_lat",
        assert_fixed=assert_fixed,
    )


def test_xmip_metadata_fix_ignores_non_cmip6():
    dataset = _raw_cmip6_dataset()
    dataset.attrs["project_id"] = "CMIP5"
    dataset.attrs["mip_era"] = "CMIP5"

    fix = woodpecker_xmip_plugin.KnownCmip6Metadata()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []
    assert fix.apply(dataset, dry_run=False) is False


def test_xmip_cmip6_preprocessing_plan_checks_and_fixes_dataset():
    dataset = _raw_cmip6_dataset()

    findings = woodpecker.plan.check(dataset, PLAN)
    assert set(findings.fix_ids) == {
        "woodpecker.rename_variables",
        "xmip.fix_known_cmip6_metadata",
    }

    preview = woodpecker.plan.fix(
        dataset,
        PLAN,
        dry_run=True,
    )
    assert preview.changed == 2
    assert "i" in dataset.dims
    assert "branch_time_in_parent" not in dataset.attrs

    write = woodpecker.plan.fix(
        dataset,
        PLAN,
        dry_run=False,
    )
    assert write.changed == 4
    assert "x" in dataset.dims
    assert "y" in dataset.dims
    assert "lon" in dataset.coords
    assert "lat" in dataset.coords
    assert float(dataset["lon"].min()) >= 0
    assert dataset.attrs["branch_time_in_parent"] == 91250
    assert not woodpecker.plan.check(dataset, PLAN)


def test_xmip_cmip6_preprocessing_plan_drops_helper_coords():
    """Adapted from xMIP's ``test_combined_preprocessing_dropped_coords``."""
    dataset = _xy_dataset_with_2d_lon_lat()
    dataset = dataset.assign_coords(
        x_bounds=xr.concat([dataset.x, dataset.x], "bnds"),
        bnds=np.arange(2),
    )

    write = woodpecker.plan.fix(
        dataset,
        PLAN,
        dry_run=False,
    )

    assert write.changed > 0
    assert "bnds" not in dataset.coords


def test_xmip_nominal_xy_plan_includes_nominal_coordinate_replacement():
    plan = woodpecker.plan.get("xmip.cmip6_preprocessing_nominal_xy")
    step_ids = [step.id for step in plan.steps]

    assert "xmip.replace_xy_with_nominal_lon_lat" in step_ids
    assert step_ids.index("xmip.replace_xy_with_nominal_lon_lat") > step_ids.index(
        "woodpecker.normalize_longitude_convention"
    )
