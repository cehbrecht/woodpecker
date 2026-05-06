"""End-to-end public API examples for CMIP6 fix plans."""

from pathlib import Path

import numpy as np
import pytest

import woodpecker
from woodpecker.testing import integration_plan_path, make_cmip6

from .helpers import assert_plan_check_fix_cycle, write_plan_document


def test_plan_checks_and_fixes_synthetic_cmip6_dataset():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()
    plan_path = integration_plan_path("cmip6_core_plan.json")

    def assert_unchanged(ds):
        assert ds["tas"].attrs["units"] == "degC"
        np.testing.assert_allclose(ds["tas"].values, original_values)

    def assert_fixed(ds):
        assert ds["tas"].attrs["units"] == "K"
        np.testing.assert_allclose(ds["tas"].values, original_values + 273.15)

    assert_plan_check_fix_cycle(
        plan_path,
        dataset,
        expected_fix_ids=("woodpecker.normalize_tas_units_to_kelvin",),
        expected_changed=1,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_plan_step_options_are_used_for_core_fixes(tmp_path: Path):
    dataset = make_cmip6()
    dataset = dataset.assign_coords(member=np.arange(dataset.sizes["lat"]))
    dataset["member_weight"] = ("member", np.ones(dataset.sizes["lat"], dtype="float32"))
    plan_path = write_plan_document(
        tmp_path / "plans.json",
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
        plan_path,
        dataset,
        expected_fix_ids=("woodpecker.merge_equivalent_dimensions",),
        expected_changed=1,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_plan_id_selects_one_plan_when_multiple_plans_match(tmp_path: Path):
    dataset = make_cmip6(overrides={"units": "degC"})
    plan_path = write_plan_document(
        tmp_path / "plans.json",
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

    with pytest.raises(ValueError, match="Multiple matching fix plans found"):
        woodpecker.check_plan(plan_path, inputs=dataset)

    findings = woodpecker.check_plan(plan_path, inputs=dataset, plan_id="cmip6.units")

    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
