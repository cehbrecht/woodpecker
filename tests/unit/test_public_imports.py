def test_public_import_surfaces_are_available():
    from woodpecker import CheckResult, FixResult, check, fix, recipe
    from woodpecker.fixes import (
        UNPRIORITIZED,
        FixFunction,
        FixFunctionRegistry,
        register_fix_function,
    )
    from woodpecker.recipes import FixRef, Recipe, load_recipe
    from woodpecker.recipes import document as build_document
    from woodpecker.recipes import fix as build_fix
    from woodpecker.recipes import match as build_match
    from woodpecker.recipes import recipe as build_recipe
    from woodpecker.runner import apply_recipe, run_fix
    from woodpecker.selection import select_fixes

    assert callable(apply_recipe)
    assert callable(check)
    assert callable(fix)
    assert callable(recipe.auto)
    assert callable(recipe.check)
    assert callable(recipe.fix)
    assert callable(recipe.get)
    assert callable(recipe.list_recipes)
    assert Recipe.__name__ == "Recipe"
    assert FixRef.__name__ == "FixRef"
    assert CheckResult.__name__ == "CheckResult"
    assert FixResult.__name__ == "FixResult"
    assert FixFunction.__name__ == "FixFunction"
    assert FixFunctionRegistry.__name__ == "FixFunctionRegistry"
    assert UNPRIORITIZED == -1
    assert callable(register_fix_function)
    assert callable(load_recipe)
    assert callable(build_fix)
    assert callable(build_match)
    assert callable(build_recipe)
    assert callable(build_document)
    assert callable(run_fix)
    assert callable(select_fixes)


def test_testing_public_api_exports_are_stable():
    from woodpecker import testing

    assert testing.__all__ == [
        "integration_recipe_path",
        "integration_root_dir",
        "make_atlas",
        "make_cmip6",
        "make_cmip6_decadal",
        "make_cmip7",
        "make_cordex",
        "repository_root",
        "testing_root_dir",
        "write_json",
        "write_recipe_document",
    ]
