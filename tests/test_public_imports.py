def test_public_import_surfaces_are_available():
    from woodpecker import CheckResult, FixResult, apply_fix_plan, check, fix
    from woodpecker.plans import load_fix_plan
    from woodpecker.runner import run_fix
    from woodpecker.selection import select_fixes

    assert callable(apply_fix_plan)
    assert callable(check)
    assert callable(fix)
    assert CheckResult.__name__ == "CheckResult"
    assert FixResult.__name__ == "FixResult"
    assert callable(load_fix_plan)
    assert callable(run_fix)
    assert callable(select_fixes)
