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


def test_testing_public_api_exports_are_stable():
    from woodpecker import testing

    assert testing.__all__ == [
        "integration_plan_path",
        "integration_root_dir",
        "make_atlas",
        "make_cmip6",
        "make_cmip6_decadal",
        "make_cmip7",
        "make_cordex",
        "repository_root",
        "testing_root_dir",
        "write_json",
        "write_plan_document",
    ]
