"""End-to-end public API examples for CMIP6 recipes."""

from pathlib import Path

import numpy as np
import pytest

import woodpecker
from woodpecker.testing import make_cmip6

from .helpers import assert_plan_check_fix_cycle, write_recipe_document


def test_plan_checks_and_fixes_synthetic_cmip6_dataset():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()

    def assert_unchanged(ds):
        assert ds["tas"].attrs["units"] == "degC"
        np.testing.assert_allclose(ds["tas"].values, original_values)

    def assert_fixed(ds):
        assert ds["tas"].attrs["units"] == "K"
        np.testing.assert_allclose(ds["tas"].values, original_values + 273.15)

    assert_plan_check_fix_cycle(
        None,
        dataset,
        expected_fix_ids=("woodpecker.normalize_tas_units_to_kelvin",),
        expected_changed=1,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
        recipe_id="cmip6.core_units",
    )


def test_plan_step_options_are_used_for_core_fixes(tmp_path: Path):
    dataset = make_cmip6()
    dataset = dataset.assign_coords(member=np.arange(dataset.sizes["lat"]))
    dataset["member_weight"] = ("member", np.ones(dataset.sizes["lat"], dtype="float32"))
    recipe_path = write_recipe_document(
        tmp_path / "recipes.json",
        [
            {
                "id": "cmip6.merge_member",
                "match": {"attrs": {"project_id": "CMIP6"}},
                "steps": [
                    {
                        "id": "woodpecker.merge_equivalent_dimensions",
                        "options": {"dims": ["lat", "member"]},
                    }
                ],
            }
        ],
    )

    def assert_unchanged(ds):
        assert ds["member_weight"].dims == ("member",)

    def assert_fixed(ds):
        assert ds["member_weight"].dims == ("lat",)

    assert_plan_check_fix_cycle(
        recipe_path,
        dataset,
        expected_fix_ids=("woodpecker.merge_equivalent_dimensions",),
        expected_changed=1,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_recipe_id_selects_one_plan_when_multiple_plans_match(tmp_path: Path):
    dataset = make_cmip6(overrides={"units": "degC"})
    recipe_path = write_recipe_document(
        tmp_path / "recipes.json",
        [
            {
                "id": "cmip6.structure",
                "match": {"attrs": {"project_id": "CMIP6"}},
                "steps": [{"id": "woodpecker.ensure_latitude_is_increasing"}],
            },
            {
                "id": "cmip6.units",
                "match": {"attrs": {"project_id": "CMIP6"}},
                "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
            },
        ],
    )

    with pytest.raises(ValueError, match="Multiple matching recipes found"):
        woodpecker.recipe.check(dataset, recipe_path)

    findings = woodpecker.recipe.check(dataset, recipe_path, recipe_id="cmip6.units")

    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
