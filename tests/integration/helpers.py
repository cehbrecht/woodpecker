import json
from pathlib import Path

from woodpecker import check, fix, plan

CORE_FIX_IDS = {
    "woodpecker.normalize_tas_units_to_kelvin",
    "woodpecker.ensure_latitude_is_increasing",
    "woodpecker.remove_coordinate_fill_value_encodings",
    "woodpecker.merge_equivalent_dimensions",
}


def write_plan_document(path: Path, plans: list[dict]) -> Path:
    path.write_text(json.dumps({"plans": plans}), encoding="utf-8")
    return path


def unique_in_order(values) -> tuple[str, ...]:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


def check_finding_ids(dataset, fix_id: str, *, fix_options=None) -> set[str]:
    result = check(
        dataset,
        fixes=fix_id,
        options=fix_options,
    )
    return set(result.fix_ids)


def assert_no_core_fixes_reported(dataset) -> None:
    assert not check(dataset, fixes=sorted(CORE_FIX_IDS)).has_findings


def assert_fix_dry_run_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, fixes=fix_id, options=fix_options, write=False)

    assert result.stats == {
        "attempted": 1,
        "changed": 1,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }


def assert_fix_write_reports_change(dataset, fix_id: str, *, fix_options=None) -> None:
    result = fix(dataset, fixes=fix_id, options=fix_options, write=True)

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


def assert_plan_check_fix_cycle(
    plan_path: Path,
    dataset,
    *,
    expected_fix_ids: tuple[str, ...],
    expected_changed: int,
    assert_fixed,
    assert_unchanged=None,
    plan_id: str | None = None,
) -> None:
    """Exercise the plan API from finding through dry-run, write, and re-check."""
    findings = plan.check(dataset, plan_path, plan_id=plan_id)

    assert unique_in_order(findings.fix_ids) == expected_fix_ids

    dry_run = plan.fix(dataset, plan_path, write=False, plan_id=plan_id)
    assert dry_run.changed == expected_changed
    assert dry_run.persisted == 0
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    write = plan.fix(dataset, plan_path, write=True, plan_id=plan_id)
    assert write.changed == expected_changed
    assert write.persisted == 1
    assert_fixed(dataset)

    assert not plan.check(dataset, plan_path, plan_id=plan_id).has_findings
