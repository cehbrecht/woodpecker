import importlib.util
import json
from pathlib import Path

import pytest


def _load_generator_module():
    module_path = Path(__file__).parents[2] / "scripts" / "generate_recipe_catalog.py"
    spec = importlib.util.spec_from_file_location("generate_recipe_catalog", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_recipe_catalog_loads_single_yaml_recipe_source(tmp_path):
    generator = _load_generator_module()
    recipe_dir = tmp_path / "recipes"
    recipe_dir.mkdir()

    (recipe_dir / "cmip6_core_recipe.yaml").write_text(
        "recipes:\n"
        "  - id: cmip6.core_units\n"
        "    match:\n"
        "      attrs:\n"
        "        project_id: CMIP6\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    md_path = tmp_path / "recipe-reference.md"
    json_path = tmp_path / "recipe-reference.json"
    generator.generate_recipe_catalog(
        md_path=str(md_path),
        json_path=str(json_path),
        recipe_dir=str(recipe_dir),
        include_plugin_recipes=False,
    )

    catalog = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert [item["id"] for item in catalog] == ["cmip6.core_units"]
    assert catalog[0]["source"] == "integration-tests"
    assert catalog[0]["source_files"] == [(recipe_dir / "cmip6_core_recipe.yaml").as_posix()]
    assert (
        f"[{(recipe_dir / 'cmip6_core_recipe.yaml').as_posix()}]"
        f"(https://github.com/cehbrecht/woodpecker/blob/main/"
        f"{(recipe_dir / 'cmip6_core_recipe.yaml').as_posix()})"
    ) in markdown
    assert "woodpecker.normalize_tas_units_to_kelvin" in markdown


def test_generate_recipe_catalog_rejects_duplicate_recipe_ids(tmp_path):
    generator = _load_generator_module()
    recipe_dir = tmp_path / "recipes"
    recipe_dir.mkdir()

    json_payload = {
        "recipes": [
            {
                "id": "cmip6.core_units",
                "match": {"attrs": {"project_id": "CMIP6"}},
                "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
            }
        ]
    }
    (recipe_dir / "cmip6_core_recipe.json").write_text(json.dumps(json_payload), encoding="utf-8")
    (recipe_dir / "cmip6_core_recipe.yaml").write_text(
        "recipes:\n"
        "  - id: cmip6.core_units\n"
        "    match:\n"
        "      attrs:\n"
        "        project_id: CMIP6\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate definition for recipe id 'cmip6.core_units'"):
        generator.load_integration_recipes(recipe_dir)


def test_generate_recipe_catalog_can_load_discovered_recipe_sources():
    generator = _load_generator_module()

    recipes = generator.load_discovered_recipes()
    recipe_by_id = {recipe.id: (recipe, source_files, source) for recipe, source_files, source in recipes}

    assert "cmip6.core_units" in recipe_by_id
    _, source_files, source = recipe_by_id["cmip6.core_units"]
    assert source == "core"
    assert source_files == ["woodpecker/recipes/recipes/cmip6_core_recipe.yaml"]

    assert "atlas.basic" in recipe_by_id
    _, source_files, source = recipe_by_id["atlas.basic"]
    assert source == "plugin:woodpecker_atlas_plugin"
    assert source_files == [
        "plugins/woodpecker-atlas-plugin/src/woodpecker_atlas_plugin/recipes/atlas_basic_recipe.json"
    ]

    assert "xmip.cmip6_preprocessing" in recipe_by_id
    recipe, source_files, source = recipe_by_id["xmip.cmip6_preprocessing"]
    assert source == "plugin:woodpecker_xmip_plugin"
    assert source_files == [
        "plugins/woodpecker-xmip-plugin/src/woodpecker_xmip_plugin/recipes/cmip6_preprocessing.yaml"
    ]
    assert "woodpecker.convert_units" in [step.id for step in recipe.steps]
