import xarray as xr

from woodpecker.fixes.cmip6_fixes import ATLAS01, CMIP6D01


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


def test_atlas01_apply_write_sets_dummy_marker_attr():
    dataset = xr.Dataset(attrs={"source_name": "atlas sample.nc"})

    fix = ATLAS01()
    changed = fix.apply(dataset, dry_run=False)

    assert changed is True
    assert dataset.attrs["woodpecker_fix_ATLAS01"] == "applied"
