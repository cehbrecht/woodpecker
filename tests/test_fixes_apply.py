from pathlib import Path

from woodpecker.fixes.cmip6_fixes import ATLAS01, CMIP6D01


def test_cmip6d01_apply_dry_run_reports_change_without_renaming(
    cmip6_member_file: Path,
):
    source = cmip6_member_file

    fix = CMIP6D01()
    changed = fix.apply(source, dry_run=True)

    assert changed is True
    assert source.exists()
    assert not source.with_name("cmip6_member_decadal.nc").exists()


def test_cmip6d01_apply_write_renames_file(
    cmip6_member_file: Path,
):
    source = cmip6_member_file

    fix = CMIP6D01()
    changed = fix.apply(source, dry_run=False)

    assert changed is True
    assert not source.exists()
    assert source.with_name("cmip6_member_decadal.nc").exists()


def test_atlas01_apply_write_replaces_spaces(
    atlas_spaced_file: Path,
):
    source = atlas_spaced_file

    fix = ATLAS01()
    changed = fix.apply(source, dry_run=False)

    assert changed is True
    assert not source.exists()
    assert source.with_name("atlas_sample.nc").exists()
