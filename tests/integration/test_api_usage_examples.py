"""Minimal public API examples using synthetic climate datasets.

This file is intentionally light on test helpers. It shows the shape user code
should normally take: build or open a dataset, run ``woodpecker.check()``, run a
dry-run ``woodpecker.fix()``, apply with ``dry_run=False``, and re-check. The recipe
example shows the same flow through ``woodpecker.recipe.check()`` and
``woodpecker.recipe.fix()``.
"""

import numpy as np

import woodpecker
from woodpecker.recipes import DatasetMatcher, FixRef, Recipe
from woodpecker.stores import AutoRecipeStore, JsonRecipeStore, RecipeCatalog
from woodpecker.testing import make_cmip6


def test_usage_example_check_and_fix_synthetic_cmip6_dataset():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()

    result = woodpecker.check(
        dataset,
        fixes="woodpecker.normalize_tas_units_to_kelvin",
    )

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    preview = woodpecker.fix(
        dataset,
        fixes="woodpecker.normalize_tas_units_to_kelvin",
        dry_run=True,
    )

    assert preview.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.fix(
        dataset,
        fixes="woodpecker.normalize_tas_units_to_kelvin",
        dry_run=False,
    )

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)

    auto_plan = woodpecker.recipe.auto("woodpecker.normalize_tas_units_to_kelvin")

    assert not woodpecker.recipe.check(dataset, auto_plan)

    assert not woodpecker.check(
        dataset,
        fixes="woodpecker.normalize_tas_units_to_kelvin",
    )


def test_usage_example_check_and_fix_synthetic_cmip6_dataset_with_plan():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()
    recipe = woodpecker.recipe.get("cmip6.core_units")

    result = woodpecker.recipe.check(dataset, recipe)

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    preview = woodpecker.recipe.fix(dataset, recipe, dry_run=True)

    assert preview.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.recipe.fix(dataset, recipe, dry_run=False)

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)

    assert not woodpecker.recipe.check(dataset, recipe)


def test_usage_example_check_and_fix_synthetic_cmip6_dataset_with_auto_plan():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()

    auto_plan = woodpecker.recipe.auto("woodpecker.normalize_tas_units_to_kelvin")

    result = woodpecker.recipe.check(dataset, auto_plan)

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    preview = woodpecker.recipe.fix(dataset, auto_plan, dry_run=True)

    assert preview.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.recipe.fix(dataset, auto_plan, dry_run=False)

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)


def test_usage_example_query_recipe_catalog(tmp_path):
    dataset = make_cmip6(overrides={"units": "degC"})
    store = JsonRecipeStore(tmp_path / "recipes.yaml")
    store.save_recipe(
        Recipe(
            id="cmip6.curated_units",
            description="Curated CMIP6 units recipe",
            match=DatasetMatcher(dataset_id_patterns=["CMIP6.CMIP.*.Amon.tas.*"]),
            steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")],
        )
    )
    catalog = RecipeCatalog([store, AutoRecipeStore()])

    matched_plans = catalog.lookup(dataset)

    assert [recipe.id for recipe in matched_plans][:2] == [
        "cmip6.curated_units",
        "woodpecker.normalize_tas_units_to_kelvin",
    ]
