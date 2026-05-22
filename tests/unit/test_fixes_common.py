import numpy as np
import xarray as xr

from woodpecker.fixes.common import (
    ConvertUnitsFix,
    DropVariablesFix,
    MergeEquivalentDimensionsFix,
    NormalizeLongitudeConventionFix,
    NormalizeTasUnitsToKelvinFix,
    PromoteMissingDimensionCoordsFix,
    RenameVariablesFix,
    SetCoordinateVariablesFix,
)


def test_common01_apply_write_converts_temperature_units_to_kelvin():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([0.0, 1.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degC"

    changed = NormalizeTasUnitsToKelvinFix().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["temp"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["temp"].values, [273.15, 274.15])


def test_common04_apply_write_merges_equivalent_dims():
    dataset = xr.Dataset(
        data_vars={"tcwv": (("time", "bnds"), np.array([[1.0, 2.0]], dtype=np.float32))},
        coords={
            "time": [0],
            "bnds": [0, 1],
            "nv": [0, 1],
        },
    )

    changed = (
        MergeEquivalentDimensionsFix()
        .configure({"dims": ["bnds", "nv"]})
        .apply(dataset, dry_run=False)
    )

    assert changed is True
    assert "bnds" in dataset["tcwv"].dims
    assert "nv" not in dataset["tcwv"].dims


def test_common05_rename_variables_uses_configured_mapping():
    dataset = xr.Dataset(
        data_vars={
            "tas": (("j", "i"), np.ones((2, 3))),
            "longitude": (("j", "i"), np.ones((2, 3))),
            "latitude": (("j", "i"), np.ones((2, 3))),
        },
        coords={"i": [0, 1, 2], "j": [0, 1]},
    )

    changed = (
        RenameVariablesFix()
        .configure(
            {
                "mapping": {
                    "x": ["i"],
                    "y": ["j"],
                    "lon": ["longitude"],
                    "lat": ["latitude"],
                }
            }
        )
        .apply(dataset, dry_run=False)
    )

    assert changed is True
    assert "x" in dataset.dims
    assert "y" in dataset.dims
    assert "lon" in dataset.data_vars
    assert "lat" in dataset.data_vars
    assert "longitude" not in dataset.variables
    assert "latitude" not in dataset.variables


def test_common05_promote_missing_dimension_coords_can_limit_dims():
    dataset = xr.Dataset(data_vars={"tas": (("x", "y"), np.ones((2, 3)))})

    changed = PromoteMissingDimensionCoordsFix().configure({"dims": ["x"]}).apply(
        dataset,
        dry_run=False,
    )

    assert changed is True
    assert "x" in dataset.coords
    assert "y" not in dataset.coords


def test_common05_set_coordinate_variables_moves_configured_variables_to_coords():
    dataset = xr.Dataset(
        data_vars={
            "tas": (("y", "x"), np.ones((2, 3))),
            "lon": (("y", "x"), np.ones((2, 3))),
        },
        coords={"x": [0, 1, 2], "y": [0, 1]},
    )

    changed = SetCoordinateVariablesFix().configure({"coordinates": ["lon"]}).apply(
        dataset,
        dry_run=False,
    )

    assert changed is True
    assert "lon" in dataset.coords


def test_common05_convert_units_uses_configured_targets():
    dataset = xr.Dataset(
        data_vars={"thetao": ("lev", np.ones(3))},
        coords={"lev": ("lev", np.array([0.0, 50.0, 100.0]), {"units": "centimeters"})},
    )

    changed = ConvertUnitsFix().configure({"units": {"lev": "m"}}).apply(
        dataset,
        dry_run=False,
    )

    assert changed is True
    np.testing.assert_allclose(dataset["lev"].values, np.array([0.0, 0.5, 1.0]))
    assert dataset["lev"].attrs["units"] == "m"


def test_common05_normalize_longitude_convention_updates_bounds():
    dataset = xr.Dataset(
        coords={
            "lon": ("x", np.array([-10.0, 0.0, 10.0])),
            "lon_bounds": (("x", "bnds"), np.array([[-11.0, -9.0], [-1.0, 1.0], [9.0, 11.0]])),
        }
    )

    changed = (
        NormalizeLongitudeConventionFix()
        .configure({"coordinate": "lon", "target": "0_360", "bounds": ["lon_bounds"]})
        .apply(dataset, dry_run=False)
    )

    assert changed is True
    assert float(dataset["lon"].min()) >= 0
    assert float(dataset["lon_bounds"].min()) >= 0


def test_common05_drop_variables_uses_configured_names():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", np.ones(2)), "helper": ("time", np.zeros(2))},
        coords={"time": [0, 1]},
    )

    changed = DropVariablesFix().configure({"variables": ["helper"]}).apply(
        dataset,
        dry_run=False,
    )

    assert changed is True
    assert "helper" not in dataset.variables
