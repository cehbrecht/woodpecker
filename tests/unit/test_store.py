from __future__ import annotations

from pathlib import Path

import pytest
import xarray as xr

from woodpecker.recipes.matcher import recipe_matches_dataset
from woodpecker.recipes.models import DatasetMatcher, FixRef, Recipe
from woodpecker.stores import (
    AutoRecipeStore,
    DuckDBRecipeStore,
    JsonRecipeStore,
    RecipeCatalog,
)
from woodpecker.testing import make_atlas, make_cmip6

UNKNOWN_PLAN_ID_ERROR = "Unknown recipe identifier"


def _sample_plan() -> Recipe:
    return Recipe(
        id="tests.plan_1",
        description="sample recipe",
        match=DatasetMatcher(
            attrs={"project_id": "CMIP6", "table_id": "Amon"},
            path_patterns=["*cmip6*.nc"],
        ),
        steps=[
            FixRef(id="woodpecker.normalize_tas_units_to_kelvin", options={"mode": "fast"}),
            FixRef(id="woodpecker.ensure_latitude_is_increasing"),
        ],
    )


def _single_step_plan(
    recipe_id: str,
    fix_id: str = "woodpecker.remove_coordinate_fill_value_encodings",
    *,
    match: DatasetMatcher | None = None,
    description: str | None = None,
) -> Recipe:
    kwargs = {"id": recipe_id, "steps": [FixRef(id=fix_id)]}
    if match is not None:
        kwargs["match"] = match
    if description is not None:
        kwargs["description"] = description
    return Recipe(**kwargs)


def _json_store(tmp_path: Path) -> JsonRecipeStore:
    return JsonRecipeStore(tmp_path / "recipes.json")


def _duckdb_store(tmp_path: Path) -> DuckDBRecipeStore:
    pytest.importorskip("duckdb")
    return DuckDBRecipeStore(tmp_path / "recipes.duckdb")


STORE_FACTORIES = [
    pytest.param(_json_store, id="json-store"),
    pytest.param(_duckdb_store, id="duckdb-store"),
]


def _assert_lookup_ids(store, dataset: xr.Dataset, *, path: str, expected_ids: list[str]) -> None:
    matched = store.lookup(dataset, path=path)
    assert [item.id for item in matched] == expected_ids


# Serialization and matcher behavior


def test_recipe_serialization_roundtrip():
    recipe = _sample_plan()

    payload = recipe.model_dump_json()
    restored = Recipe.model_validate_json(payload)

    assert restored == recipe
    assert restored.steps[0].id == "woodpecker.normalize_tas_units_to_kelvin"
    assert restored.steps[0].options == {"mode": "fast"}


def test_plan_matcher_requires_both_attrs_and_path_when_both_defined():
    recipe = _sample_plan()
    ds = make_cmip6()

    assert recipe_matches_dataset(recipe, ds, path="/tmp/data/cmip6_case.nc") is True
    assert recipe_matches_dataset(recipe, ds, path="/tmp/data/other_case.nc") is False


def test_plan_matcher_general_applicability_without_matcher():
    recipe = Recipe(
        id="tests.plan_any", steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")]
    )
    ds = xr.Dataset(attrs={"anything": "value"})

    assert recipe_matches_dataset(recipe, ds) is True


def test_plan_matcher_attrs_only():
    recipe = Recipe(
        id="tests.plan_attrs",
        match=DatasetMatcher(attrs={"project_id": "CMIP7"}),
        steps=[FixRef(id="cmip7.ensure_project_id_present")],
    )

    assert recipe_matches_dataset(recipe, xr.Dataset(attrs={"project_id": "CMIP7"})) is True
    assert recipe_matches_dataset(recipe, make_cmip6()) is False


def test_plan_matcher_path_only():
    recipe = Recipe(
        id="tests.recipe_path",
        match=DatasetMatcher(path_patterns=["*.zarr", "*decadal*.nc"]),
        steps=[FixRef(id="woodpecker.ensure_latitude_is_increasing")],
    )
    ds = xr.Dataset()

    assert recipe_matches_dataset(recipe, ds, path="/tmp/case.zarr") is True
    assert recipe_matches_dataset(recipe, ds, path="/tmp/c3s-decadal.nc") is True
    assert recipe_matches_dataset(recipe, ds, path="/tmp/case.nc") is False
    assert recipe_matches_dataset(recipe, ds, path=None) is False


def test_plan_matcher_dataset_id_patterns():
    recipe = Recipe(
        id="tests.plan_dataset_id",
        match=DatasetMatcher(dataset_id_patterns=["CMIP6.CMIP.*.Amon.tas.*"]),
        steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")],
    )

    assert recipe_matches_dataset(recipe, make_cmip6()) is True
    assert (
        recipe_matches_dataset(
            recipe,
            xr.Dataset(attrs={"dataset_id": "CMIP6.DCPP.Model.dcppA-hindcast.s1960.Amon.tas.gn"}),
        )
        is False
    )
    assert recipe_matches_dataset(recipe, xr.Dataset()) is False


def test_auto_store_lists_registered_fixes_as_single_step_plans():
    store = AutoRecipeStore()

    recipes = store.list_recipes()
    recipe = store.get_recipe("woodpecker.tas_units_to_kelvin")

    assert "woodpecker.normalize_tas_units_to_kelvin" in {item.id for item in recipes}
    assert recipe.id == "woodpecker.normalize_tas_units_to_kelvin"
    assert recipe.steps[0].id == "woodpecker.normalize_tas_units_to_kelvin"


def test_auto_store_lookup_uses_fix_matches_and_dataset_type():
    store = AutoRecipeStore()
    dataset = make_cmip6(overrides={"units": "degC"})

    matched = store.lookup(dataset)

    assert "woodpecker.normalize_tas_units_to_kelvin" in [recipe.id for recipe in matched]


def test_auto_store_is_read_only():
    store = AutoRecipeStore()

    with pytest.raises(NotImplementedError, match="read-only"):
        store.save_recipe(_single_step_plan("tests.recipe"))


def test_recipe_catalog_lists_sources_and_deduplicates_by_id(tmp_path):
    explicit_store = JsonRecipeStore(tmp_path / "recipes.json")
    explicit_store.save_recipe(
        _single_step_plan(
            "woodpecker.normalize_tas_units_to_kelvin",
            description="curated recipe wins",
        )
    )
    explicit_store.save_recipe(_single_step_plan("tests.extra"))
    catalog = RecipeCatalog([explicit_store, AutoRecipeStore()])

    recipes = catalog.list_recipes()
    recipe_ids = [recipe.id for recipe in recipes]

    assert recipe_ids.count("woodpecker.normalize_tas_units_to_kelvin") == 1
    assert "tests.extra" in recipe_ids
    assert catalog.get_recipe("woodpecker.tas_units_to_kelvin").description == "curated recipe wins"


def test_recipe_catalog_lookup_queries_all_sources(tmp_path):
    explicit_store = JsonRecipeStore(tmp_path / "recipes.json")
    explicit_store.save_recipe(
        _single_step_plan(
            "cmip6.curated_units",
            "woodpecker.normalize_tas_units_to_kelvin",
            match=DatasetMatcher(attrs={"project_id": "CMIP6"}),
        )
    )
    catalog = RecipeCatalog([explicit_store, AutoRecipeStore()])
    dataset = make_cmip6(overrides={"units": "degC"})

    matched = catalog.lookup(dataset)

    matched_ids = [recipe.id for recipe in matched]
    assert matched_ids[:2] == [
        "cmip6.curated_units",
        "woodpecker.normalize_tas_units_to_kelvin",
    ]


def test_recipe_catalog_is_read_only():
    catalog = RecipeCatalog([])

    with pytest.raises(NotImplementedError, match="read-only"):
        catalog.save_recipe(_single_step_plan("tests.recipe"))


@pytest.mark.parametrize(
    ("filename", "schema_marker"),
    [
        ("recipes.json", '"schema_version": 1'),
        ("recipes.yaml", "schema_version: 1"),
    ],
)
def test_json_store_save_list_lookup(tmp_path, filename, schema_marker):
    store = JsonRecipeStore(tmp_path / filename)
    plan_1 = _sample_plan()
    plan_2 = _single_step_plan("tests.plan_2")

    store.save_recipe(plan_1)
    store.save_recipe(plan_2)

    raw = store.path.read_text(encoding="utf-8")
    assert schema_marker in raw

    listed = store.list_recipes()
    assert [item.id for item in listed] == ["tests.plan_1", "tests.plan_2"]

    ds = make_cmip6()
    _assert_lookup_ids(
        store,
        ds,
        path="/tmp/cmip6_case.nc",
        expected_ids=["tests.plan_1", "tests.plan_2"],
    )
    _assert_lookup_ids(store, ds, path="/tmp/no-match.txt", expected_ids=["tests.plan_2"])


# JSON store behavior


def test_json_store_lookup_matches_atlas_fixture(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")
    atlas_plan = _single_step_plan(
        "atlas.lookup",
        "atlas.encoding_cleanup",
        match=DatasetMatcher(
            attrs={"project_id": "C3S-Atlas"},
            path_patterns=["*atlas*.nc"],
        ),
    )
    catchall_plan = _single_step_plan("tests.catchall")

    store.save_recipe(atlas_plan)
    store.save_recipe(catchall_plan)

    matched = store.lookup(make_atlas(), path="/tmp/atlas_case.nc")

    assert [item.id for item in matched] == ["atlas.lookup", "tests.catchall"]


def test_json_store_save_replaces_existing_recipe_id(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")

    store.save_recipe(
        _single_step_plan(
            "tests.plan_1",
            "woodpecker.normalize_tas_units_to_kelvin",
            description="old",
        )
    )
    store.save_recipe(
        _single_step_plan(
            "tests.plan_1",
            "woodpecker.ensure_latitude_is_increasing",
            description="new",
        )
    )

    listed = store.list_recipes()
    assert len(listed) == 1
    assert listed[0].description == "new"
    assert listed[0].steps[0].id == "woodpecker.ensure_latitude_is_increasing"


def test_json_store_save_upserts_by_recipe_id(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")

    store.save_recipe(
        Recipe(
            id="atlas.cleanup_plan",
            description="old",
            steps=[FixRef(id="atlas.encoding_cleanup")],
        )
    )
    store.save_recipe(
        Recipe(
            id="atlas.cleanup_plan",
            description="new",
            steps=[FixRef(id="atlas.project_id_normalization")],
        )
    )

    listed = store.list_recipes()
    assert len(listed) == 1
    assert listed[0].id == "atlas.cleanup_plan"
    assert listed[0].description == "new"


def test_json_store_save_normalizes_prefix_and_suffix_recipe_id(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")
    store.save_recipe(
        Recipe.model_validate(
            {
                "prefix": "atlas",
                "suffix": "cleanup_plan",
                "steps": [{"id": "encoding_cleanup"}],
            }
        )
    )

    listed = store.list_recipes()
    raw = store.path.read_text(encoding="utf-8")

    assert listed[0].id == "atlas.cleanup_plan"
    assert listed[0].steps[0].id == "atlas.encoding_cleanup"
    assert '"id": "atlas.cleanup_plan"' in raw
    assert "suffix" not in raw


@pytest.mark.parametrize("store_factory", STORE_FACTORIES)
def test_store_get_recipe_resolves_id(tmp_path, store_factory):
    store = store_factory(tmp_path)
    recipe = Recipe(id="atlas.cleanup_plan", steps=[FixRef(id="atlas.encoding_cleanup")])
    store.save_recipe(recipe)

    by_id = store.get_recipe("atlas.cleanup_plan")
    assert by_id.id == "atlas.cleanup_plan"

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_recipe("cleanup_plan")


@pytest.mark.parametrize("store_factory", STORE_FACTORIES)
def test_store_get_recipe_resolves_aliases(tmp_path, store_factory):
    store = store_factory(tmp_path)
    recipe = Recipe(
        id="atlas.cleanup_plan",
        aliases=["cleanup", "legacy.cleanup_plan"],
        steps=[FixRef(id="atlas.encoding_cleanup")],
    )
    store.save_recipe(recipe)

    by_qualified_alias = store.get_recipe("atlas.cleanup")
    by_legacy_alias = store.get_recipe("legacy.cleanup_plan")

    assert by_qualified_alias.id == "atlas.cleanup_plan"
    assert by_legacy_alias.id == "atlas.cleanup_plan"

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_recipe("cleanup")


def test_json_store_get_recipe_rejects_unqualified_suffix(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")
    store.save_recipe(
        Recipe(id="alpha.shared", steps=[FixRef(id="woodpecker.ensure_latitude_is_increasing")])
    )
    store.save_recipe(
        Recipe(id="beta.shared", steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")])
    )

    with pytest.raises(ValueError, match=UNKNOWN_PLAN_ID_ERROR):
        store.get_recipe("shared")


def test_json_store_get_recipe_detects_duplicate_ids(tmp_path):
    store = JsonRecipeStore(tmp_path / "recipes.json")
    store.path.write_text(
        '{"recipes": [{"id": "atlas.cleanup_plan", "steps": [{"id": "atlas.encoding_cleanup"}]}, {"id": "atlas.cleanup_plan", "steps": [{"id": "atlas.project_id_normalization"}]}]}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate recipe id detected"):
        store.get_recipe("atlas.cleanup_plan")


# DuckDB store behavior


def test_duckdb_store_save_list_lookup(tmp_path):
    store = _duckdb_store(tmp_path)
    plan_1 = _sample_plan()
    plan_2 = _single_step_plan("tests.plan_2")

    store.save_recipe(plan_1)
    store.save_recipe(plan_2)

    listed = store.list_recipes()
    assert [item.id for item in listed] == ["tests.plan_1", "tests.plan_2"]

    ds = make_cmip6()
    _assert_lookup_ids(
        store,
        ds,
        path="/tmp/cmip6_case.nc",
        expected_ids=["tests.plan_1", "tests.plan_2"],
    )
    _assert_lookup_ids(store, ds, path="/tmp/no-match.txt", expected_ids=["tests.plan_2"])


def test_duckdb_store_save_list_lookup_in_memory():
    pytest.importorskip("duckdb")

    store = DuckDBRecipeStore()
    plan_1 = _sample_plan()
    plan_2 = _single_step_plan("tests.plan_2")

    store.save_recipe(plan_1)
    store.save_recipe(plan_2)

    listed = store.list_recipes()
    assert [item.id for item in listed] == ["tests.plan_1", "tests.plan_2"]

    ds = make_cmip6()
    _assert_lookup_ids(
        store,
        ds,
        path="/tmp/cmip6_case.nc",
        expected_ids=["tests.plan_1", "tests.plan_2"],
    )
    _assert_lookup_ids(store, ds, path="/tmp/no-match.txt", expected_ids=["tests.plan_2"])

    store.close()


def test_duckdb_lookup_skips_decoding_nonmatching_fixes_payload(tmp_path):
    duckdb = pytest.importorskip("duckdb")

    db_path = tmp_path / "recipes.duckdb"
    store = DuckDBRecipeStore(db_path)
    store.save_recipe(
        Recipe(
            id="atlas.lookup_atlas",
            match=DatasetMatcher(path_patterns=["*atlas*.nc"]),
            steps=[FixRef(id="atlas.encoding_cleanup")],
        )
    )
    store.save_recipe(
        Recipe(
            id="cmip6.lookup_cmip6",
            match=DatasetMatcher(path_patterns=["*cmip6*.nc"]),
            steps=[FixRef(id="cmip6.dummy_placeholder")],
        )
    )

    # Corrupt a non-matching row to verify lookup does not decode its steps payload.
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "UPDATE recipes SET steps_json = ? WHERE id = ?",
            ["not-json", "cmip6.lookup_cmip6"],
        )

    matched = store.lookup(xr.Dataset(), path="/tmp/atlas_case.nc")
    assert [item.id for item in matched] == ["atlas.lookup_atlas"]


def test_duckdb_store_raises_clear_error_when_dependency_missing(tmp_path, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "duckdb":
            raise ImportError("duckdb not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(RuntimeError, match="requires optional dependency 'duckdb'"):
        DuckDBRecipeStore(tmp_path / "missing.duckdb")
