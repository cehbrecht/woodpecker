from woodpecker import check, fix


def check_finding_ids(dataset, fix_id: str) -> set[str]:
    return set(check(dataset, fixes=fix_id).fix_ids)


def assert_check_fix_cycle(dataset, fix_id: str, *, assert_fixed, assert_unchanged=None) -> None:
    assert check_finding_ids(dataset, fix_id) == {fix_id}

    dry_run = fix(dataset, fixes=fix_id, dry_run=True)
    assert dry_run.changed == 1
    assert dry_run.persisted == 0
    if assert_unchanged is not None:
        assert_unchanged(dataset)

    write = fix(dataset, fixes=fix_id, dry_run=False)
    assert write.changed == 1
    assert write.persisted == 1
    assert_fixed(dataset)

    assert check_finding_ids(dataset, fix_id) == set()
