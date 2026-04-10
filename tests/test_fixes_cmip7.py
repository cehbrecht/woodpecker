import numpy as np
import xarray as xr

from woodpecker.fixes.cmip7 import CMIP7_0001, CMIP7_0002, CMIP7_0003
from woodpecker.fixes.cmip7.helpers import project_id_from_dataset
from woodpecker.fixes.common.helpers import get_data_unit, is_celsius_unit


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


def test_cmip702_apply_write_sets_project_id_from_source_name_when_missing():
    dataset = xr.Dataset(attrs={"source_name": "CMIP7.Model.member.tas.nc"})

    changed = CMIP7_0001().apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["project_id"] == "CMIP7"


def test_cmip703_apply_write_renames_temp_to_tas_when_tas_missing():
    dataset = xr.Dataset(
        data_vars={"temp": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )

    changed = CMIP7_0002().apply(dataset, dry_run=False)

    assert changed is True
    assert "tas" in dataset.data_vars
    assert "temp" not in dataset.data_vars


def test_cmip704_apply_write_uses_variable_map_parameter():
    dataset = xr.Dataset(
        data_vars={"prw": ("time", np.array([1.0, 2.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )

    fix = CMIP7_0003().configure({"variable_map": {"prw": "tcwv"}})
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "tcwv" in dataset.data_vars
    assert "prw" not in dataset.data_vars


def test_cmip705_apply_write_uses_dim_map_and_metadata_parameters():
    dataset = xr.Dataset(
        data_vars={"tcwv": (("time", "bnds"), np.array([[1.0, 2.0]], dtype=np.float32))},
        coords={
            "time": [0],
            "bnds": [0, 1],
        },
    )

    fix = CMIP7_0003().configure(
        {
            "dim_map": {"bnds": "nv"},
            "realm": "atmos",
            "branded_variable": "prw_tavg-u-hxy-u",
        }
    )
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "nv" in dataset["tcwv"].dims
    assert "bnds" not in dataset["tcwv"].dims
    assert dataset.attrs["realm"] == "atmos"
    assert dataset.attrs["branded_variable"] == "prw_tavg-u-hxy-u"


def test_cmip706_apply_write_can_clear_global_attrs_when_requested():
    dataset = xr.Dataset(
        data_vars={"prw": ("time", np.array([1.0], dtype=np.float32))},
        coords={"time": [0]},
        attrs={"source": "original", "history": "old"},
    )

    fix = CMIP7_0003().configure(
        {
            "variable_map": {"prw": "tcwv"},
            "keep_global_attrs": False,
            "realm": "atmos",
        }
    )
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert set(dataset.attrs.keys()) == {"realm"}
    assert "tcwv" in dataset.data_vars
