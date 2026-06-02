from pathlib import Path

import pytest
import xarray as xr

from woodpecker.fixes.registry import FixFunction, FixFunctionRegistry, register_fix_function
from woodpecker.recipes.matcher import recipe_matches_dataset
from woodpecker.recipes.models import (
    FixRef,
    ProviderMetadata,
    Recipe,
    RecipeDocument,
    RecipeRuntimeMetadata,
)
from woodpecker.runner import apply_recipe
from woodpecker.stores.json_store import JsonRecipeStore
from woodpecker.testing import make_cmip6, write_json


def _load_document(path: Path, payload: dict) -> RecipeDocument:
    write_json(path, payload)
    return RecipeDocument(recipes=JsonRecipeStore(path).list_recipes())


class _FixMethod(FixFunction):
    prefix = "plan_test"
    suffix = "fix_method"
    name = "Recipe fix method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def matches(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("matches", dict(getattr(self, "config", {}))))
        return True

    def apply(self, dataset, dry_run=True):
        dataset.attrs.setdefault("trace", []).append(
            ("apply", dict(getattr(self, "config", {})), dry_run)
        )
        return True


class _ApplyMethod(FixFunction):
    prefix = "plan_test"
    suffix = "apply_method"
    name = "Recipe apply method"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def configure(self, config=None):
        self.config = dict(config or {})
        return self

    def matches(self, dataset):
        dataset.attrs.setdefault("trace", []).append(("matches", dict(getattr(self, "config", {}))))
        return True

    def apply(self, dataset, dry_run=True):
        dataset.attrs.setdefault("trace", []).append(
            ("apply", dict(getattr(self, "config", {})), dry_run)
        )
        return True


class _TypeErrorInsideMethod(FixFunction):
    prefix = "plan_test"
    suffix = "type_error_inside_method"
    name = "Recipe type error fix"
    description = ""
    categories = ["metadata"]
    priority = 10
    dataset = None

    def check(self, dataset):
        raise TypeError("check should not be called")

    def matches(self, dataset):
        return True

    def apply(self, dataset, dry_run=True):
        return True


# Recipe file parsing and normalization


def test_load_recipe_from_json(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(
        '{"id": "plan_test.default_plan", "steps": [{"id": "plan_test.fix_method", "options": {"mode": "fast"}}, "plan_test.apply_method"]}',
        encoding="utf-8",
    )

    recipes = JsonRecipeStore(recipe_path).list_recipes()
    recipe = recipes[0]

    assert isinstance(recipe, Recipe)
    assert [f.id for f in recipe.steps] == ["plan_test.fix_method", "plan_test.apply_method"]
    assert recipe.steps[0].options == {"mode": "fast"}
    assert recipe.steps[1].options == {}


def test_load_recipe_from_yaml(tmp_path: Path):
    recipe_path = tmp_path / "recipe.yaml"
    recipe_path.write_text(
        "id: plan_test.default_plan\nsteps:\n  - id: plan_test.fix_method\n    options:\n      level: strict\n",
        encoding="utf-8",
    )

    recipes = JsonRecipeStore(recipe_path).list_recipes()
    recipe = recipes[0]

    assert [f.id for f in recipe.steps] == ["plan_test.fix_method"]
    assert recipe.steps[0].options == {"level": "strict"}


def test_apply_plan_calls_matches_then_apply_and_passes_options():
    register_fix_function(_FixMethod)
    ds = make_cmip6()
    recipe = Recipe.model_validate(
        {
            "id": "plan_test.execution_order",
            "steps": [{"id": "plan_test.fix_method", "options": {"alpha": 1}}],
        }
    )

    apply_recipe(ds, recipe, FixFunctionRegistry)

    assert ds.attrs["trace"] == [("matches", {"alpha": 1}), ("apply", {"alpha": 1}, False)]


def test_apply_plan_uses_apply_for_execution():
    register_fix_function(_ApplyMethod)
    ds = make_cmip6()
    recipe = Recipe.model_validate(
        {
            "id": "plan_test.apply_fallback",
            "steps": [{"id": "plan_test.apply_method", "options": {"beta": 2}}],
        }
    )

    apply_recipe(ds, recipe, FixFunctionRegistry)

    assert ds.attrs["trace"] == [("matches", {"beta": 2}), ("apply", {"beta": 2}, False)]


def test_apply_plan_does_not_call_check():
    register_fix_function(_TypeErrorInsideMethod)
    ds = make_cmip6()
    recipe = Recipe.model_validate(
        {
            "id": "plan_test.type_error_passthrough",
            "steps": [{"id": "plan_test.type_error_inside_method", "options": {"gamma": 3}}],
        }
    )

    apply_recipe(ds, recipe, FixFunctionRegistry)


def test_load_recipe_document_json(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "recipes": [
                {
                    "id": "cmip6.basic",
                    "description": "simple recipe",
                    "match": {"path_patterns": ["*cmip6*.nc"]},
                    "steps": [{"id": "CMIP6_0001", "options": {"message": "ok"}}],
                }
            ]
        },
    )

    assert isinstance(document, RecipeDocument)
    assert document.schema_version == 1
    assert len(document.recipes) == 1
    assert document.recipes[0].id == "cmip6.basic"
    assert document.recipes[0].steps[0].id == "cmip6.cmip6_0001"


def test_load_recipe_document_dataset_id_patterns(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "recipes": [
                {
                    "id": "cmip6.dataset_id_match",
                    "match": {"dataset_id_patterns": ["CMIP6.CMIP.*.Amon.tas.*"]},
                    "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                }
            ]
        },
    )

    assert document.recipes[0].match is not None
    assert document.recipes[0].match.dataset_id_patterns == ["CMIP6.CMIP.*.Amon.tas.*"]


def test_load_recipe_document_single_plan_shorthand(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "id": "atlas.single",
            "steps": [{"id": "CMIP6_0001"}],
        },
    )

    assert document.schema_version == 1
    assert len(document.recipes) == 1
    assert document.recipes[0].id == "atlas.single"
    assert document.recipes[0].steps[0].id == "atlas.cmip6_0001"


def test_load_recipe_document_plan_entries_normalize_fix_ids(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "recipes": [
                {
                    "id": "atlas.mixed_case",
                    "steps": [
                        {
                            "id": "cmip6.dummy_placeholder",
                            "options": {"marker_attr": "my_marker"},
                        },
                        {"id": "atlas.encoding_cleanup", "options": {}},
                    ],
                }
            ]
        },
    )

    fixes = document.recipes[0].steps
    assert [item.id for item in fixes] == ["cmip6.dummy_placeholder", "atlas.encoding_cleanup"]
    assert fixes[0].options["marker_attr"] == "my_marker"


def test_recipe_to_dict_persists_ids_from_suffix_fix_refs():
    recipe = Recipe.model_validate(
        {
            "id": "atlas.atlas_basic",
            "steps": [
                {"id": "encoding_cleanup", "options": {"mode": "strict"}},
                {"id": "atlas.project_id_normalization", "options": {}},
            ],
        }
    )

    payload = recipe.model_dump()

    assert [item.id for item in recipe.steps] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert [item["id"] for item in payload["steps"]] == [
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ]
    assert payload["steps"][0]["options"] == {"mode": "strict"}
    assert payload["id"] == "atlas.atlas_basic"
    assert "namespace" not in payload
    assert "suffix" not in payload


# Recipe identity and alias behavior


def test_fix_recipe_identity_uses_identifier_set_when_prefix_and_suffix_available():
    recipe = Recipe(id="atlas.atlas_basic", steps=[FixRef(id="atlas.encoding_cleanup")])

    assert recipe.identifier_set is not None
    assert recipe.identifier_set.prefix == "atlas"
    assert recipe.identifier_set.suffix == "atlas_basic"
    assert recipe.identifier_set.id == "atlas.atlas_basic"
    assert recipe.prefix == "atlas"


def test_fix_recipe_identity_can_be_built_from_prefix_and_suffix():
    recipe = Recipe.model_validate(
        {
            "prefix": "atlas",
            "suffix": "atlas_basic",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    assert recipe.id == "atlas.atlas_basic"
    assert recipe.prefix == "atlas"
    assert recipe.suffix == "atlas_basic"
    assert [item.id for item in recipe.steps] == ["atlas.encoding_cleanup"]


def test_fix_recipe_identity_rejects_unqualified_id():
    with pytest.raises(ValueError, match="Expected '<prefix>.<suffix>'"):
        Recipe.model_validate(
            {
                "prefix": "atlas",
                "id": "atlas_basic",
                "steps": [{"id": "encoding_cleanup"}],
            }
        )


def test_fix_recipe_identity_persists_id_only():
    recipe = Recipe.model_validate(
        {
            "prefix": "atlas",
            "suffix": "atlas_basic",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    payload = recipe.model_dump()

    assert payload["id"] == "atlas.atlas_basic"
    assert "prefix" not in payload
    assert "suffix" not in payload


def test_fix_recipe_identity_rejects_conflicting_explicit_parts():
    with pytest.raises(ValueError, match="suffix does not match"):
        Recipe.model_validate(
            {
                "id": "atlas.basic",
                "suffix": "other",
                "steps": [{"id": "encoding_cleanup"}],
            }
        )


def test_fix_recipe_identity_includes_aliases():
    recipe = Recipe(
        id="atlas.atlas_basic",
        aliases=["basic", "legacy.atlas_basic"],
        steps=[FixRef(id="atlas.encoding_cleanup")],
    )

    assert recipe.aliases == ["atlas.basic", "legacy.atlas_basic"]
    assert recipe.identifier_set.aliases == (
        "atlas.basic",
        "legacy.atlas_basic",
    )


def test_recipe_namespace_scopes_unqualified_fix_refs():
    recipe = Recipe.model_validate(
        {
            "id": "atlas.atlas_plan",
            "steps": [{"id": "encoding_cleanup"}],
        }
    )

    assert recipe.prefix == "atlas"
    assert [item.id for item in recipe.steps] == ["atlas.encoding_cleanup"]


def test_recipe_runtime_metadata_provider_is_available_but_not_persisted():
    recipe = Recipe(
        id="cmip7.esa_cci_water_vapour_zarr",
        steps=[FixRef(id="cmip7.configurable_reformat_bridge")],
        runtime_metadata=RecipeRuntimeMetadata(
            provider=ProviderMetadata(name="woodpecker-cmip7-plugin", version="0.4.2")
        ),
    )

    runtime_payload = recipe.runtime_metadata_dump()
    assert runtime_payload == {"provider": {"name": "woodpecker-cmip7-plugin", "version": "0.4.2"}}

    persisted = recipe.model_dump()
    assert "runtime_metadata" not in persisted


def test_recipe_document_description_fields_are_parsed(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "recipes": [
                {
                    "id": "atlas.with_description",
                    "description": "Dataset selector note",
                    "steps": [{"id": "CMIP6_0001", "options": {"message": "selector message"}}],
                }
            ]
        },
    )

    assert document.recipes[0].description == "Dataset selector note"


def test_recipe_document_uses_explicit_schema_version_when_present(tmp_path: Path):
    recipe_path = tmp_path / "recipe.json"
    document = _load_document(
        recipe_path,
        {
            "schema_version": 1,
            "recipes": [
                {
                    "id": "atlas.basic",
                    "steps": [{"id": "atlas.encoding_cleanup"}],
                }
            ],
        },
    )

    assert document.schema_version == 1
    assert document.recipes[0].id == "atlas.basic"


def test_recipe_document_to_dict_includes_schema_version():
    document = RecipeDocument(
        recipes=[Recipe(id="atlas.basic", steps=[FixRef(id="atlas.encoding_cleanup")])]
    )

    payload = document.model_dump()

    assert payload["schema_version"] == 1
    assert payload["recipes"][0]["id"] == "atlas.basic"


def test_cmip7_plan_document_uses_plugin_fix_codes_in_order(tmp_path):
    recipe_path = tmp_path / "recipes.json"
    document = _load_document(
        recipe_path,
        {
            "recipes": [
                {
                    "id": "cmip7.synthetic_reformat",
                    "match": {"path_patterns": ["*.zarr"]},
                    "steps": [
                        {"id": "cmip7.configurable_reformat_bridge"},
                        {"id": "woodpecker.ensure_latitude_is_increasing"},
                    ],
                }
            ]
        },
    )
    assert len(document.recipes) == 1

    ds = xr.Dataset()
    target = "/tmp/CMIP7.CMIP.synthetic.case.zarr"
    matched = [
        recipe for recipe in document.recipes if recipe_matches_dataset(recipe, ds, path=target)
    ]

    assert matched
    recipe = matched[0]
    assert [recipe.resolve_fix_identifier(item) for item in recipe.steps] == [
        "cmip7.configurable_reformat_bridge",
        "woodpecker.ensure_latitude_is_increasing",
    ]
