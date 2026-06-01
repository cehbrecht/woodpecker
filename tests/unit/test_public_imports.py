def test_public_import_surfaces_are_available():
    from woodpecker import CheckResult, FixResult, check, fix, plan
    from woodpecker.fix_plans import FixPlan, FixRef, load_fix_plan
    from woodpecker.fix_plans import document as build_document
    from woodpecker.fix_plans import fix as build_fix
    from woodpecker.fix_plans import match as build_match
    from woodpecker.fix_plans import plan as build_plan
    from woodpecker.fixes import (
        UNPRIORITIZED,
        FixFunction,
        FixFunctionRegistry,
        register_fix_function,
    )
    from woodpecker.runner import apply_fix_plan, run_fix
    from woodpecker.selection import select_fixes

    assert callable(apply_fix_plan)
    assert callable(check)
    assert callable(fix)
    assert callable(plan.auto)
    assert callable(plan.check)
    assert callable(plan.fix)
    assert callable(plan.get)
    assert callable(plan.list_plans)
    assert FixPlan.__name__ == "FixPlan"
    assert FixRef.__name__ == "FixRef"
    assert CheckResult.__name__ == "CheckResult"
    assert FixResult.__name__ == "FixResult"
    assert FixFunction.__name__ == "FixFunction"
    assert FixFunctionRegistry.__name__ == "FixFunctionRegistry"
    assert UNPRIORITIZED == -1
    assert callable(register_fix_function)
    assert callable(load_fix_plan)
    assert callable(build_fix)
    assert callable(build_match)
    assert callable(build_plan)
    assert callable(build_document)
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
