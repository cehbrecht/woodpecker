import json

import yaml

from woodpecker.recipes import document, fix, match, recipe
from woodpecker.recipes.builder import FixStepBuilder, RecipeBuilder, RecipeDocumentBuilder
from woodpecker.recipes.models import Recipe, RecipeDocument


def test_fix_step_builder_creates_fix_ref_with_options_and_links():
    step = fix(
        "woodpecker.convert_units",
        {"units": {"tas": "K"}},
        dry_run_only=False,
        links=({"rel": "docs", "href": "https://example.invalid"},),
    )

    ref = step.to_model()

    assert isinstance(step, FixStepBuilder)
    assert ref.id == "woodpecker.convert_units"
    assert ref.options == {"units": {"tas": "K"}, "dry_run_only": False}
    assert ref.links[0].rel == "docs"


def test_recipe_builder_creates_existing_recipe_model():
    built = recipe(
        "cmip6.core_units",
        fix("woodpecker.normalize_tas_units_to_kelvin"),
        description="Core units recipe",
    ).match(
        attrs={"project_id": "CMIP6"},
        dataset_id_patterns=["CMIP6.CMIP.*.Amon.tas.*"],
    )

    model = built.to_model()

    assert isinstance(built, RecipeBuilder)
    assert isinstance(model, Recipe)
    assert model.id == "cmip6.core_units"
    assert model.description == "Core units recipe"
    assert model.match is not None
    assert model.match.attrs == {"project_id": "CMIP6"}
    assert model.steps[0].id == "woodpecker.normalize_tas_units_to_kelvin"


def test_recipe_builder_scopes_local_fix_ids_to_plan_prefix():
    model = recipe("atlas.basic", "encoding_cleanup").to_model()

    assert model.steps[0].id == "atlas.encoding_cleanup"


def test_recipe_builder_accepts_match_builder_and_step_mappings():
    model = recipe(
        "atlas.basic",
        {"id": "encoding_cleanup", "options": {"mode": "strict"}},
        match=match(path_patterns=["*atlas*.nc"]),
    ).to_model()

    assert model.match is not None
    assert model.match.path_patterns == ["*atlas*.nc"]
    assert model.steps[0].id == "atlas.encoding_cleanup"
    assert model.steps[0].options == {"mode": "strict"}


def test_recipe_builder_serializes_as_recipe_document_json_and_yaml(tmp_path):
    built = recipe("atlas.basic", fix("encoding_cleanup", mode="strict"))
    json_path = tmp_path / "recipe.json"
    yaml_path = tmp_path / "recipe.yaml"

    json_text = built.to_json(json_path)
    yaml_text = built.to_yaml(yaml_path)

    json_payload = json.loads(json_text)
    yaml_payload = yaml.safe_load(yaml_text)

    assert json_payload == yaml_payload
    assert json_payload["recipes"][0]["id"] == "atlas.basic"
    assert json_payload["recipes"][0]["steps"][0]["id"] == "atlas.encoding_cleanup"
    assert json_path.read_text(encoding="utf-8") == json_text
    assert yaml.safe_load(yaml_path.read_text(encoding="utf-8")) == yaml_payload


def test_document_builder_combines_multiple_python_plans():
    built = document(
        recipe("atlas.basic", "encoding_cleanup"),
        recipe("cmip6.core_units", "woodpecker.normalize_tas_units_to_kelvin"),
    )

    model = built.to_model()

    assert isinstance(built, RecipeDocumentBuilder)
    assert isinstance(model, RecipeDocument)
    assert [recipe.id for recipe in model.recipes] == ["atlas.basic", "cmip6.core_units"]
    assert json.loads(built.to_json())["recipes"][1]["id"] == "cmip6.core_units"
