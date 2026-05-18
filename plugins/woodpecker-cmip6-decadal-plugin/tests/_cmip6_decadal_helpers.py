from pathlib import Path

from woodpecker import check, fix, plan


def check_finding_ids(dataset, fix_id: str) -> set[str]:
    return set(check(dataset, fixes=fix_id).fix_ids)


def assert_fix_dry_run_reports_change(dataset, fix_id: str) -> None:
    result = fix(dataset, fixes=fix_id, dry_run=True)

    assert result.changed == 1
    assert result.persisted == 0


def assert_fix_write_reports_change(dataset, fix_id: str) -> None:
    result = fix(dataset, fixes=fix_id, dry_run=False)

    assert result.changed == 1
    assert result.persisted == 1


def assert_check_fix_cycle(dataset, fix_id: str, *, assert_fixed) -> None:
    assert check_finding_ids(dataset, fix_id) == {fix_id}

    assert_fix_dry_run_reports_change(dataset, fix_id)
    assert_fix_write_reports_change(dataset, fix_id)
    assert_fixed(dataset)

    assert check_finding_ids(dataset, fix_id) == set()


def unique_in_order(values) -> tuple[str, ...]:
    out = []
    for value in values:
        if value not in out:
            out.append(value)
    return tuple(out)


def assert_plan_check_fix_cycle(
    plan_path: Path,
    dataset,
    *,
    expected_fix_ids: tuple[str, ...],
    expected_changed: int,
    expected_write_changed: int | None = None,
    assert_fixed,
    assert_unchanged=None,
) -> None:
    findings = plan.check(dataset, plan_path)
    assert unique_in_order(findings.fix_ids) == expected_fix_ids

    preview = plan.fix(dataset, plan_path, dry_run=True)
    assert preview.changed == expected_changed
    assert preview.persisted == 0
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    write = plan.fix(dataset, plan_path, dry_run=False)
    assert write.changed == (expected_changed if expected_write_changed is None else expected_write_changed)
    assert write.persisted == 1
    assert_fixed(dataset)

    assert not plan.check(dataset, plan_path)
