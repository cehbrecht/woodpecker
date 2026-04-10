import numpy as np
import pytest
import xarray as xr

from woodpecker.fixes.atlas import ATLAS_0001, ATLAS_0002
from woodpecker.fixes.cmip6 import CMIP6_0001
from woodpecker.fixes.cmip6_decadal import (
    CMIP6D_0001,
    CMIP6D_0002,
    CMIP6D_0003,
    CMIP6D_0004,
    CMIP6D_0005,
    CMIP6D_0006,
    CMIP6D_0007,
    CMIP6D_0008,
    CMIP6D_0009,
    CMIP6D_0010,
    CMIP6D_0011,
    CMIP6D_0012,
    CMIP6D_0013,
    CMIP6D_0014,
    CMIP6D_0015,
)
from woodpecker.fixes.common import COMMON_0001


def test_cmip601_dummy_apply_write_sets_dummy_marker_attr():
    dataset = xr.Dataset(attrs={"source_name": "cmip6_member.nc"})

    fix = CMIP6_0001()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["woodpecker_fix_CMIP6_0001"] == "applied"


def test_cmip6d01_apply_dry_run_reports_change_without_writing_dataset_attrs():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": 2},
    )

    fix = CMIP6D_0001()
    changed = fix.apply(dataset, dry_run=True)

    assert changed is True
    assert dataset["time"].attrs.get("long_name") is None
    assert "realization" not in dataset.data_vars


def test_cmip6d01_apply_write_sets_simple_decadal_metadata_fixes():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": "2"},
    )

    fix = CMIP6D_0001()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["time"].attrs["long_name"] == "valid_time"


def test_cmip6d02_apply_write_normalizes_proleptic_calendar():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["time"].encoding["calendar"] = "proleptic_gregorian"

    fix = CMIP6D_0002()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["time"].encoding["calendar"] == "standard"


def test_cmip6d02_apply_write_converts_cftime_proleptic_values_when_available():
    cftime = pytest.importorskip("cftime")
    dataset = xr.Dataset(
        coords={
            "time": [
                cftime.DatetimeProlepticGregorian(1960, 11, 1),
                cftime.DatetimeProlepticGregorian(1960, 11, 2),
            ]
        },
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["time"].encoding["calendar"] = "proleptic_gregorian"

    fix = CMIP6D_0002()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert isinstance(dataset["time"].values[0], cftime.DatetimeGregorian)
    assert dataset["time"].encoding["calendar"] == "standard"


def test_cmip6d03_apply_write_adds_realization_variable():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": "2"},
    )

    fix = CMIP6D_0003()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "realization" in dataset.data_vars
    assert int(dataset["realization"].values) == 2


@pytest.mark.parametrize(
    "fix_cls",
    [
        CMIP6D_0001,
        CMIP6D_0002,
        CMIP6D_0003,
        CMIP6D_0004,
        CMIP6D_0005,
        CMIP6D_0006,
        CMIP6D_0007,
        CMIP6D_0008,
        CMIP6D_0009,
        CMIP6D_0010,
        CMIP6D_0011,
        CMIP6D_0012,
        CMIP6D_0013,
        CMIP6D_0014,
        CMIP6D_0015,
    ],
)
def test_cmip6_decadal_fixes_do_not_match_non_decadal_cmip6(fix_cls):
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6.member.tas.nc", "realization_index": "2"},
    )

    fix = fix_cls()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []


def test_cmip6d04_apply_write_removes_coordinates_encoding_from_decadal_vars():
    dataset = xr.Dataset(
        data_vars={
            "realization": xr.DataArray(2),
            "lon_bnds": (("x", "bnds"), [[0.0, 1.0]]),
            "lat_bnds": (("x", "bnds"), [[10.0, 11.0]]),
            "time_bnds": (("time", "bnds"), [[0.0, 1.0]]),
        },
        coords={"time": [0], "x": [0], "bnds": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["realization"].encoding["coordinates"] = "time"
    dataset["lon_bnds"].encoding["coordinates"] = "lon lat"
    dataset["lat_bnds"].encoding["coordinates"] = "lat lon"
    dataset["time_bnds"].encoding["coordinates"] = "time"

    fix = CMIP6D_0004()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["realization"].encoding.get("coordinates") is None
    assert dataset["lon_bnds"].encoding.get("coordinates") is None
    assert dataset["lat_bnds"].encoding.get("coordinates") is None
    assert dataset["time_bnds"].encoding.get("coordinates") is None


def test_cmip6d05_apply_write_normalizes_realization_comment():
    dataset = xr.Dataset(
        data_vars={"realization": xr.DataArray(2, attrs={"long_name": "realization"})},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["realization"].attrs["comment"] = (
        "For more information on the ripf, refer to variant_label and global attributes."
    )

    fix = CMIP6D_0005()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["realization"].attrs["comment"] == (
        "For more information on the ripf, refer to the variant_label, "
        "initialization_description, physics_description and forcing_description "
        "global attributes"
    )


def test_cmip6d06_apply_write_normalizes_realization_dtype_to_int32():
    dataset = xr.Dataset(
        data_vars={"realization": xr.DataArray(2)},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["realization"].encoding["coordinates"] = "time"

    fix = CMIP6D_0006()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["realization"].dtype == np.int32
    assert dataset["realization"].encoding.get("coordinates") == "time"


def test_cmip6d07_apply_write_removes_fillvalue_encoding_from_decadal_vars():
    dataset = xr.Dataset(
        data_vars={
            "realization": xr.DataArray(2),
            "lon_bnds": (("x", "bnds"), [[0.0, 1.0]]),
            "lat_bnds": (("x", "bnds"), [[10.0, 11.0]]),
            "time_bnds": (("time", "bnds"), [[0.0, 1.0]]),
        },
        coords={"time": [0], "x": [0], "bnds": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["realization"].encoding["_FillValue"] = -9999
    dataset["lon_bnds"].encoding["_FillValue"] = -9999.0
    dataset["lat_bnds"].encoding["_FillValue"] = -9999.0
    dataset["time_bnds"].encoding["_FillValue"] = -9999.0

    fix = CMIP6D_0007()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "_FillValue" not in dataset["realization"].encoding
    assert "_FillValue" not in dataset["lon_bnds"].encoding
    assert "_FillValue" not in dataset["lat_bnds"].encoding
    assert "_FillValue" not in dataset["time_bnds"].encoding


def test_cmip6d08_apply_write_normalizes_further_info_url_variant_separator():
    dataset = xr.Dataset(
        attrs={
            "source_name": "c3s-cmip6-decadal.member.tas.nc",
            "further_info_url": (
                "https://furtherinfo.es-doc.org/CMIP6.EC-Earth-Consortium.EC-Earth3."
                "dcppA-hindcast.s1960-r2i1p1f1"
            ),
        }
    )

    fix = CMIP6D_0008()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["further_info_url"] == (
        "https://furtherinfo.es-doc.org/CMIP6.EC-Earth-Consortium.EC-Earth3."
        "dcppA-hindcast.s1960.r2i1p1f1"
    )


def test_cmip6d09_apply_write_normalizes_startdate_and_sub_experiment_id():
    dataset = xr.Dataset(
        attrs={
            "source_name": (
                "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3."
                "dcppA-hindcast.s1960-r2i1p1f1.Amon.tas.gr.v20201215.nc"
            ),
            "startdate": "s1960",
            "sub_experiment_id": "s1960",
        }
    )

    fix = CMIP6D_0009()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["startdate"] == "s196011"
    assert dataset.attrs["sub_experiment_id"] == "s196011"


def test_cmip6d10_apply_write_normalizes_realization_long_name():
    dataset = xr.Dataset(
        data_vars={"realization": xr.DataArray(2, attrs={"long_name": "member"})},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )

    fix = CMIP6D_0010()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["realization"].attrs["long_name"] == "realization"


def test_cmip6d11_apply_write_normalizes_realization_index_type_to_int():
    dataset = xr.Dataset(
        attrs={
            "source_name": "c3s-cmip6-decadal.member.tas.nc",
            "realization_index": "2",
        }
    )

    fix = CMIP6D_0011()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["realization_index"] == 2
    assert isinstance(dataset.attrs["realization_index"], int)


def test_cmip6d12_apply_write_normalizes_leadtime_metadata_attrs():
    dataset = xr.Dataset(
        coords={"leadtime": ("time", [0.0, 1.0]), "time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["leadtime"].attrs["units"] = "hours"
    dataset["leadtime"].attrs["long_name"] = "lead"

    fix = CMIP6D_0012()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["leadtime"].attrs["units"] == "days"
    assert dataset["leadtime"].attrs["long_name"] == "Time elapsed since the start of the forecast"
    assert dataset["leadtime"].attrs["standard_name"] == "forecast_period"


def test_cmip6d13_apply_write_sets_model_specific_global_attrs():
    dataset = xr.Dataset(
        attrs={
            "source_name": "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1960-r2i1p1f1.Amon.tas.gr.v20201215.nc",
            "forcing_description": "wrong",
        }
    )

    fix = CMIP6D_0013()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["forcing_description"] == "f1, CMIP6 historical forcings"
    assert dataset.attrs["physics_description"].startswith("physics from the standard model")
    assert dataset.attrs["initialization_description"].startswith(
        "Atmosphere initialization based on full-fields"
    )


def test_cmip6d14_apply_write_adds_reftime_coordinate():
    dataset = xr.Dataset(
        coords={"time": np.array(["1960-11-16", "1960-12-16"], dtype="datetime64[D]")},
        attrs={
            "source_name": "c3s-cmip6-decadal.DCPP.EC-Earth-Consortium.EC-Earth3.dcppA-hindcast.s1960-r2i1p1f1.Amon.tas.gr.v20201215.nc",
            "startdate": "s196011",
        },
    )
    dataset["time"].encoding["calendar"] = "standard"

    fix = CMIP6D_0014()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "reftime" in dataset.coords
    assert dataset["reftime"].ndim == 0
    assert str(np.asarray(dataset["reftime"].values).astype("datetime64[D]")) == "1960-11-01"
    assert dataset["reftime"].attrs["standard_name"] == "forecast_reference_time"


def test_cmip6d15_apply_write_derives_leadtime_values_from_time_and_reftime():
    dataset = xr.Dataset(
        coords={"time": np.array(["1960-11-16", "1960-12-16"], dtype="datetime64[D]")},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset.coords["reftime"] = xr.DataArray(np.datetime64("1960-11-01"))

    fix = CMIP6D_0015()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "leadtime" in dataset.coords
    assert np.allclose(dataset["leadtime"].values, np.array([15.0, 45.0]))
    assert dataset["leadtime"].attrs["units"] == "days"


def test_atlas01_apply_dry_run_reports_change_without_mutating_dataset():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1], "member_id": ("time", ["r1", "r1"])},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    dataset["tas"].encoding["complevel"] = 4
    dataset["time"].encoding["_FillValue"] = -9999
    dataset["member_id"].encoding["zlib"] = True

    fix = ATLAS_0001()
    changed = fix.apply(dataset, dry_run=True)

    assert changed is True
    assert dataset["tas"].encoding["complevel"] == 4
    assert dataset["time"].encoding["_FillValue"] == -9999
    assert dataset["member_id"].encoding["zlib"] is True
    assert "project_id" not in dataset.attrs


def test_atlas01_apply_write_performs_real_encoding_fixes_only():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1], "member_id": ("time", ["r1", "r1"])},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    dataset["tas"].encoding["complevel"] = 4
    dataset["time"].encoding["_FillValue"] = -9999
    dataset["member_id"].encoding["zlib"] = True
    dataset["member_id"].encoding["shuffle"] = True
    dataset["member_id"].encoding["complevel"] = 5

    fix = ATLAS_0001()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["time"].encoding["_FillValue"] is None
    assert "zlib" not in dataset["member_id"].encoding
    assert "shuffle" not in dataset["member_id"].encoding
    assert "complevel" not in dataset["member_id"].encoding
    assert dataset["tas"].encoding["complevel"] == 1
    assert dataset["tas"].encoding["zlib"] is True
    assert dataset["tas"].encoding["shuffle"] is True
    assert "project_id" not in dataset.attrs


def test_atlas02_apply_write_sets_project_id_only():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    dataset["tas"].encoding["complevel"] = 4

    fix = ATLAS_0002()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["project_id"] == "c3s-ipcc-atlas"
    assert dataset["tas"].encoding["complevel"] == 4


def test_common01_apply_dry_run_reports_change_without_mutating_dataset():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", np.array([10.0, 11.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["tas"].attrs["units"] = "degreeC"

    fix = COMMON_0001()
    changed = fix.apply(dataset, dry_run=True)

    assert changed is True
    assert dataset["tas"].attrs["units"] == "degreeC"
    np.testing.assert_allclose(dataset["tas"].values, [10.0, 11.0])


def test_common01_apply_write_converts_celsius_to_kelvin_for_tas_variable():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", np.array([0.0, 2.0], dtype=np.float32))},
        coords={"time": [0, 1]},
    )
    dataset["tas"].attrs["units"] = "degreeC"

    fix = COMMON_0001()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, [273.15, 275.15])
