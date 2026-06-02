from __future__ import annotations

import json

import woodpecker
from woodpecker.recipes import RECIPE_PATH_ENV, RecipeLoader
from woodpecker.testing import make_cmip6


def test_recipe_loader_discovers_core_and_plugin_package_recipes():
    recipe_ids = {recipe.id for recipe in RecipeLoader().catalog().list_recipes()}

    assert "cmip6.core_units" in recipe_ids
    assert "atlas.basic" in recipe_ids
    assert "cmip6_decadal.full" in recipe_ids
    assert "cmip7.esa_cci_water_vapour_zarr" in recipe_ids
    assert "xmip.cmip6_preprocessing" in recipe_ids


def test_recipe_loader_includes_explicit_directory_before_package_recipes(tmp_path):
    (tmp_path / "recipes.yaml").write_text(
        "recipes:\n"
        "  - id: local.override\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    recipes = RecipeLoader().catalog(explicit_locations=[tmp_path]).list_recipes()

    assert recipes[0].id == "local.override"


def test_recipe_loader_includes_env_path(monkeypatch, tmp_path):
    path = tmp_path / "recipes.json"
    path.write_text(
        json.dumps(
            {
                "recipes": [
                    {
                        "id": "env.units",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(RECIPE_PATH_ENV, str(path))

    recipe_ids = {recipe.id for recipe in RecipeLoader().catalog().list_recipes()}

    assert "env.units" in recipe_ids


def test_recipe_loader_ignores_plugin_without_recipe_directory():
    sources = RecipeLoader(
        core_packages=(),
        plugin_packages=("woodpecker_cmip6_plugin",),
    ).load_documents()

    assert sources == []


def test_recipe_api_resolves_discovered_recipe_id_without_explicit_path():
    dataset = make_cmip6(overrides={"units": "degC"})

    findings = woodpecker.recipe.check(dataset, None, recipe_id="cmip6.core_units")

    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)


def test_recipe_api_get_returns_plan_usable_by_check_and_fix():
    dataset = make_cmip6(overrides={"units": "degC"})
    recipe = woodpecker.recipe.get("cmip6.core_units")

    findings = woodpecker.recipe.check(dataset, recipe)
    preview = woodpecker.recipe.fix(dataset, recipe, dry_run=True)

    assert recipe.id == "cmip6.core_units"
    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
    assert preview.changed == 1


def test_recipe_api_lists_discovered_recipes():
    recipe_ids = {recipe.id for recipe in woodpecker.recipe.list_recipes()}

    assert "cmip6.core_units" in recipe_ids
    assert "xmip.cmip6_preprocessing" in recipe_ids


def test_recipe_api_catalog_selector_resolves_plugin_recipe():
    dataset = make_cmip6(
        overrides={
            "source_id": "GFDL-CM4",
            "experiment_id": "historical",
        }
    )

    findings = woodpecker.recipe.check(
        dataset, woodpecker.recipe.catalog("xmip.cmip6_preprocessing")
    )

    assert "xmip.fix_known_cmip6_metadata" in findings.fix_ids
