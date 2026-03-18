import xarray as xr
import pytest

from woodpecker.fixes.atlas import ATLAS01, ATLAS02
from woodpecker.fixes.cmip6 import CMIP601
from woodpecker.fixes.cmip6_decadal import CMIP6D01, CMIP6D02, CMIP6D03


def test_cmip601_dummy_apply_write_sets_dummy_marker_attr():
    dataset = xr.Dataset(attrs={"source_name": "cmip6_member.nc"})

    fix = CMIP601()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["woodpecker_fix_CMIP601"] == "applied"


def test_cmip6d01_apply_dry_run_reports_change_without_writing_dataset_attrs():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": 2},
    )

    fix = CMIP6D01()
    changed = fix.apply(dataset, dry_run=True)

    assert changed is True
    assert dataset["time"].attrs.get("long_name") is None
    assert "realization" not in dataset.data_vars


def test_cmip6d01_apply_write_sets_simple_decadal_metadata_fixes():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": "2"},
    )

    fix = CMIP6D01()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["time"].attrs["long_name"] == "valid_time"


def test_cmip6d02_apply_write_normalizes_proleptic_calendar():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc"},
    )
    dataset["time"].encoding["calendar"] = "proleptic_gregorian"

    fix = CMIP6D02()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset["time"].encoding["calendar"] == "standard"


def test_cmip6d03_apply_write_adds_realization_variable():
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6-decadal.member.tas.nc", "realization_index": "2"},
    )

    fix = CMIP6D03()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert "realization" in dataset.data_vars
    assert int(dataset["realization"].values) == 2


@pytest.mark.parametrize("fix_cls", [CMIP6D01, CMIP6D02, CMIP6D03])
def test_cmip6_decadal_fixes_do_not_match_non_decadal_cmip6(fix_cls):
    dataset = xr.Dataset(
        coords={"time": [0, 1]},
        attrs={"source_name": "c3s-cmip6.member.tas.nc", "realization_index": "2"},
    )

    fix = fix_cls()

    assert fix.matches(dataset) is False
    assert fix.check(dataset) == []


def test_atlas01_apply_dry_run_reports_change_without_mutating_dataset():
    dataset = xr.Dataset(
        data_vars={"tas": ("time", [273.1, 274.2])},
        coords={"time": [0, 1], "member_id": ("time", ["r1", "r1"])},
        attrs={"source_name": "c3s-ipcc-atlas.dataset.tas.nc"},
    )
    dataset["tas"].encoding["complevel"] = 4
    dataset["time"].encoding["_FillValue"] = -9999
    dataset["member_id"].encoding["zlib"] = True

    fix = ATLAS01()
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

    fix = ATLAS01()
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

    fix = ATLAS02()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["project_id"] == "c3s-ipcc-atlas"
    assert dataset["tas"].encoding["complevel"] == 4
