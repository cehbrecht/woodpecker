import numpy as np
import xarray as xr

from woodpecker.fixes.cmip7 import CMIP701, CMIP702, CMIP703, CMIP704, CMIP705
from woodpecker.fixes.cmip7.common import get_data_unit, is_celsius_unit, project_id_from_dataset


def test_cmip7_common_is_celsius_unit_accepts_supported_spellings():
    assert is_celsius_unit("degreeC") is True
    assert is_celsius_unit("degC") is True
    assert is_celsius_unit("C") is True
    assert is_celsius_unit("degrees_c") is True
    assert is_celsius_unit("celsius") is True


def test_cmip7_common_is_celsius_unit_rejects_kelvin_and_empty_values():
    assert is_celsius_unit("K") is False
    assert is_celsius_unit("") is False
    assert is_celsius_unit(None) is False


def test_cmip7_common_get_data_unit_prefers_attrs_over_encoding():
    dataset = xr.Dataset(data_vars={"tas": ("time", [1.0])}, coords={"time": [0]})
    dataset["tas"].attrs["units"] = "degreeC"
    dataset["tas"].encoding["units"] = "K"

    assert get_data_unit(dataset, "tas") == "degreeC"


def test_cmip7_common_project_id_from_dataset_prefers_first_identifier_token():
    dataset = xr.Dataset(attrs={"dataset_id": "CMIP7.CMIP.CCCma.SomeModel"})

    assert project_id_from_dataset(dataset) == "CMIP7"


def test_cmip701_apply_write_converts_temp_when_tas_not_present():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([1.0, 2.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["temp"].attrs["units"] = "degC"

    changed = CMIP701().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["temp"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["temp"].values, [274.15, 275.15])


def test_cmip702_apply_write_sets_project_id_from_source_name_when_missing():
    dataset = xr.Dataset(attrs={"source_name": "CMIP7.Model.member.tas.nc"})

    changed = CMIP702().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["project_id"] == "CMIP7"


def test_cmip703_apply_write_renames_temp_to_tas_when_tas_missing():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )

    changed = CMIP703().apply(dataset, dry_run=False)

    assert changed is True
    assert "tas" in dataset.data_vars
    assert "temp" not in dataset.data_vars


def test_cmip704_apply_write_flips_decreasing_lat_and_lat_bounds():
    dataset = xr.Dataset(
        data_vars={
            "tas": (("lat", "lon"), np.array([[1.0], [2.0]], dtype=np.float32)),
            "lat_bnds": (("lat", "bnds"), np.array([[10.0, 5.0], [5.0, 0.0]])),
        },
        coords={"lat": np.array([7.0, 2.0]), "lon": [0], "bnds": [0, 1]},
    )
    dataset["lat"].attrs["bounds"] = "lat_bnds"

    changed = CMIP704().apply(dataset, dry_run=False)

    assert changed is True
    np.testing.assert_allclose(dataset["lat"].values, [2.0, 7.0])
    np.testing.assert_allclose(dataset["tas"].values[:, 0], [2.0, 1.0])


def test_cmip705_apply_write_removes_fillvalue_from_common_coords():
    dataset = xr.Dataset(
        data_vars={"tas": (("time", "lat", "lon"), np.zeros((1, 2, 2), dtype=np.float32))},
        coords={"time": [0], "lat": [1.0, 2.0], "lon": [10.0, 20.0]},
    )
    dataset["time"].encoding["_FillValue"] = -9999
    dataset["lat"].encoding["_FillValue"] = -9999.0
    dataset["lon"].encoding["_FillValue"] = -9999.0

    changed = CMIP705().apply(dataset, dry_run=False)

    assert changed is True
    assert "_FillValue" not in dataset["time"].encoding
    assert "_FillValue" not in dataset["lat"].encoding
    assert "_FillValue" not in dataset["lon"].encoding
