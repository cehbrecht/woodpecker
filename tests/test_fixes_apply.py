from pathlib import Path

from woodpecker.fixes.cmip6_fixes import ATLAS01, CMIP6D01


def test_cmip6d01_apply_dry_run_reports_change_without_renaming(tmp_path: Path):
    source = tmp_path / "cmip6_member.nc"
    source.write_text("placeholder", encoding="utf-8")

    fix = CMIP6D01()
    changed = fix.apply(source, dry_run=True)

    assert changed is True
    assert source.exists()
    assert not (tmp_path / "cmip6_member_decadal.nc").exists()


def test_cmip6d01_apply_write_renames_file(tmp_path: Path):
    source = tmp_path / "cmip6_member.nc"
    source.write_text("placeholder", encoding="utf-8")

    fix = CMIP6D01()
    changed = fix.apply(source, dry_run=False)

    assert changed is True
    assert not source.exists()
    assert (tmp_path / "cmip6_member_decadal.nc").exists()


def test_atlas01_apply_write_replaces_spaces(tmp_path: Path):
    source = tmp_path / "atlas sample.nc"
    source.write_text("placeholder", encoding="utf-8")

    fix = ATLAS01()
    changed = fix.apply(source, dry_run=False)

    assert changed is True
    assert not source.exists()
    assert (tmp_path / "atlas_sample.nc").exists()
