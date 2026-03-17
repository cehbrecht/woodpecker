import xarray as xr

from woodpecker.fixes.atlas import ATLAS01, ATLAS02
from woodpecker.fixes.cmip6_fixes import CMIP6D01


def test_cmip6d01_apply_dry_run_reports_change_without_writing_dataset_attrs():
    dataset = xr.Dataset(attrs={"source_name": "cmip6_member.nc"})

    fix = CMIP6D01()
    changed = fix.apply(dataset, dry_run=True)

    assert changed is True
    assert "woodpecker_fix_CMIP6D01" not in dataset.attrs


def test_cmip6d01_apply_write_sets_dummy_marker_attr():
    dataset = xr.Dataset(attrs={"source_name": "cmip6_member.nc"})

    fix = CMIP6D01()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["woodpecker_fix_CMIP6D01"] == "applied"


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
