import json
from pathlib import Path

from woodpecker import check, fix

CORE_FIX_IDS = {
    "woodpecker.normalize_tas_units_to_kelvin",
    "woodpecker.ensure_latitude_is_increasing",
    "woodpecker.remove_coordinate_fill_value_encodings",
    "woodpecker.merge_equivalent_dimensions",
}


def write_plan_document(path: Path, plans: list[dict]) -> Path:
    path.write_text(json.dumps({"plans": plans}), encoding="utf-8")
    return path


def check_finding_ids(dataset, fix_id: str, *, fix_options=None) -> set[str]:
    result = check(
        dataset,
        identifiers=[fix_id],
        fix_options=fix_options,
    )
    return set(result.fix_ids)


def assert_no_core_fixes_reported(dataset) -> None:
    assert not check(dataset, identifiers=sorted(CORE_FIX_IDS)).has_findings


def assert_fix_dry_run_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=False)

    assert result.stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }


def assert_fix_write_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=True)

    assert result.stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 1,
        "persisted": 1,
        "persist_failed": 0,
    }


def assert_check_fix_cycle(
    dataset,
    fix_id: str,
    *,
    assert_fixed,
    assert_unchanged=None,
    fix_options=None,
) -> None:
    """Exercise the public API from finding through dry-run, write, and re-check."""
    assert check_finding_ids(dataset, fix_id, fix_options=fix_options) == {fix_id}

    assert_fix_dry_run_reports_change(dataset, fix_id, fix_options=fix_options)
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    assert_fix_write_reports_change(dataset, fix_id, fix_options=fix_options)
    assert_fixed(dataset)

    assert check_finding_ids(dataset, fix_id, fix_options=fix_options) == set()
