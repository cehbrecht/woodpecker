from woodpecker import check, fix

CORE_FIX_IDS = {
    "woodpecker.normalize_tas_units_to_kelvin",
    "woodpecker.ensure_latitude_is_increasing",
    "woodpecker.remove_coordinate_fill_value_encodings",
    "woodpecker.merge_equivalent_dimensions",
}


def check_finding_ids(dataset, fix_id: str, *, fix_options=None) -> set[str]:
    return {
        item["fix_id"]
        for item in check(
            dataset,
            identifiers=[fix_id],
            fix_options=fix_options,
        )
    }


def assert_no_core_fixes_reported(dataset) -> None:
    assert check(dataset, identifiers=sorted(CORE_FIX_IDS)) == []


def assert_fix_dry_run_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    stats = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=False)

    assert stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }


def assert_fix_write_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    stats = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=True)

    assert stats == {
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
