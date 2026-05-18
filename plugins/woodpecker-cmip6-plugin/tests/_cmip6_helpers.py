from woodpecker import check, fix


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
