from woodpecker import check, fix

CORE_FIX_IDS = {
    "woodpecker.normalize_tas_units_to_kelvin",
    "woodpecker.ensure_latitude_is_increasing",
    "woodpecker.remove_coordinate_fill_value_encodings",
    "woodpecker.merge_equivalent_dimensions",
}


def core_finding_ids(dataset, *, fix_options=None) -> set[str]:
    return {
        item["fix_id"]
        for item in check(
            dataset,
            identifiers=sorted(CORE_FIX_IDS),
            fix_options=fix_options,
        )
    }


def selected_finding_ids(dataset, fix_id: str, *, fix_options=None) -> set[str]:
    return {
        item["fix_id"]
        for item in check(
            dataset,
            identifiers=[fix_id],
            fix_options=fix_options,
        )
    }


def assert_dry_run_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    stats = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=False)

    assert stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }


def assert_write_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    stats = fix(dataset, identifiers=[fix_id], fix_options=fix_options, write=True)

    assert stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 1,
        "persisted": 1,
        "persist_failed": 0,
    }


def assert_public_api_fix_flow(
    dataset,
    fix_id: str,
    *,
    assert_unchanged,
    assert_fixed,
    fix_options=None,
) -> None:
    assert selected_finding_ids(dataset, fix_id, fix_options=fix_options) == {fix_id}

    assert_dry_run_reports_change(dataset, fix_id, fix_options=fix_options)
    assert_unchanged(dataset)

    assert_write_reports_change(dataset, fix_id, fix_options=fix_options)
    assert_fixed(dataset)

    assert selected_finding_ids(dataset, fix_id, fix_options=fix_options) == set()
