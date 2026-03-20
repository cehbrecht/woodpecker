import numpy as np
import xarray as xr

from woodpecker.fixes.esmval import ESMVAL01, ESMVAL02, ESMVAL03, ESMVAL04, ESMVAL05
from woodpecker.fixes.esmval.common import get_data_unit, is_celsius_unit, project_id_from_dataset


def test_esmval_common_is_celsius_unit_accepts_supported_spellings():
    assert is_celsius_unit("degreeC") is True
    assert is_celsius_unit("degC") is True
    assert is_celsius_unit("C") is True
    assert is_celsius_unit("degrees_c") is True
    assert is_celsius_unit("celsius") is True


def test_esmval_common_is_celsius_unit_rejects_kelvin_and_empty_values():
    assert is_celsius_unit("K") is False
    assert is_celsius_unit("") is False
    assert is_celsius_unit(None) is False


def test_esmval_common_get_data_unit_prefers_attrs_over_encoding():
    dataset = xr.Dataset(data_vars={"tas": ("time", [1.0])}, coords={"time": [0]})
    dataset["tas"].attrs["units"] = "degreeC"
    dataset["tas"].encoding["units"] = "K"

    assert get_data_unit(dataset, "tas") == "degreeC"


def test_esmval_common_project_id_from_dataset_prefers_first_identifier_token():
    dataset = xr.Dataset(attrs={"dataset_id": "CMIP7.CMIP.CCCma.SomeModel"})

    assert project_id_from_dataset(dataset) == "CMIP7"


def test_esmval01_matches_uses_encoding_units_when_attrs_missing():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", np.array([0.0, 1.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["tas"].encoding["units"] = "degC"

    fix = ESMVAL01()

    assert fix.matches(dataset) is True


def test_esmval01_check_returns_empty_for_already_kelvin_dataset():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", np.array([273.15, 274.15], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["tas"].attrs["units"] = "K"

    fix = ESMVAL01()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []
    assert fix.apply(dataset, dry_run=False) is False


def test_esmval01_check_message_mentions_temp_when_temp_is_target_variable():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degreeC"

    fix = ESMVAL01()
    findings = fix.check(dataset)

    assert len(findings) == 1
    assert findings[0].startswith("temp should use Kelvin units")


def test_esmval01_apply_write_converts_temp_when_tas_not_present():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([1.0, 2.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degC"

    fix = ESMVAL01()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["temp"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["temp"].values, [274.15, 275.15])


def test_esmval01_apply_write_prefers_tas_when_both_tas_and_temp_present():
    dataset = xr.Dataset(
        data_vars={
            "tas": ("time", np.array([0.0, 1.0], dtype=np.float32)),
            "temp": ("time", np.array([5.0, 6.0], dtype=np.float32)),
        },
        coords={"time": [0, 1]},
    )
    dataset["tas"].attrs["units"] = "degreeC"
    dataset["temp"].attrs["units"] = "degreeC"

    fix = ESMVAL01()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, [273.15, 274.15])
    assert dataset["temp"].attrs["units"] == "degreeC"
    np.testing.assert_allclose(dataset["temp"].values, [5.0, 6.0])


def test_esmval02_apply_write_sets_project_id_from_source_name_when_missing():
    dataset = xr.Dataset(attrs={"source_name": "CMIP6.EC-Earth3.member.tas.nc"})

    fix = ESMVAL02()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["project_id"] == "CMIP6"


def test_esmval02_apply_noop_when_project_id_already_present():
    dataset = xr.Dataset(
        attrs={
            "dataset_id": "CMIP7.CMIP.CCCma.SomeModel",
            "project_id": "CMIP7",
        }
    )

    fix = ESMVAL02()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []
    assert fix.apply(dataset, dry_run=False) is False


def test_esmval03_apply_write_renames_temp_to_tas_when_tas_missing():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "K"

    fix = ESMVAL03()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "tas" in dataset.data_vars
    assert "temp" not in dataset.data_vars
    np.testing.assert_allclose(dataset["tas"].values, [10.0, 11.0])
    assert dataset["tas"].attrs["units"] == "K"


def test_esmval03_noop_when_tas_already_present():
    dataset = xr.Dataset(
        data_vars={
            "tas": ("time", np.array([1.0, 2.0], dtype=np.float32)),
            "temp": ("time", np.array([3.0, 4.0], dtype=np.float32)),
        },
        coords={"time": [0, 1]},
    )

    fix = ESMVAL03()

    assert fix.matches(dataset) is False
    assert fix.apply(dataset, dry_run=False) is False


def test_esmval04_apply_write_flips_decreasing_lat_and_lat_bounds():
    dataset = xr.Dataset(
        data_vars={
            "tas": (("lat", "lon"), np.array([[1.0], [2.0]], dtype=np.float32)),
            "lat_bnds": (("lat", "bnds"), np.array([[10.0, 5.0], [5.0, 0.0]])),
        },
        coords={"lat": np.array([7.0, 2.0]), "lon": [0], "bnds": [0, 1]},
    )
    dataset["lat"].attrs["bounds"] = "lat_bnds"

    fix = ESMVAL04()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    np.testing.assert_allclose(dataset["lat"].values, [2.0, 7.0])
    np.testing.assert_allclose(dataset["tas"].values[:, 0], [2.0, 1.0])
    np.testing.assert_allclose(dataset["lat_bnds"].values, [[0.0, 5.0], [5.0, 10.0]])


def test_esmval04_noop_for_increasing_latitude():
    dataset = xr.Dataset(
        data_vars={"tas": (("lat",), np.array([1.0, 2.0], dtype=np.float32))},
        coords={"lat": np.array([1.0, 2.0])},
    )

    fix = ESMVAL04()

    assert fix.matches(dataset) is False
    assert fix.apply(dataset, dry_run=False) is False


def test_esmval05_apply_write_removes_fillvalue_from_common_coords():
    dataset = xr.Dataset(
        data_vars={"tas": (("time", "lat", "lon"), np.zeros((1, 2, 2), dtype=np.float32))},
        coords={"time": [0], "lat": [1.0, 2.0], "lon": [10.0, 20.0]},
    )
    dataset["time"].encoding["_FillValue"] = -9999
    dataset["lat"].encoding["_FillValue"] = -9999.0
    dataset["lon"].encoding["_FillValue"] = -9999.0

    fix = ESMVAL05()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "_FillValue" not in dataset["time"].encoding
    assert "_FillValue" not in dataset["lat"].encoding
    assert "_FillValue" not in dataset["lon"].encoding


def test_esmval05_noop_when_no_coord_fillvalue_exists():
    dataset = xr.Dataset(
        data_vars={"tas": (("time",), np.array([1.0], dtype=np.float32))},
        coords={"time": [0]},
    )

    fix = ESMVAL05()

    assert fix.matches(dataset) is False
    assert fix.apply(dataset, dry_run=False) is False
