def test_public_import_surfaces_are_available():
    from woodpecker import apply_fix_plan
    from woodpecker.plans import load_fix_plan
    from woodpecker.runner import run_fix
    from woodpecker.selection import select_fixes

    assert callable(apply_fix_plan)
    assert callable(load_fix_plan)
    assert callable(run_fix)
    assert callable(select_fixes)
