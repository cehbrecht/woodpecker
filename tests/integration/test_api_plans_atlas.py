"""End-to-end public API examples for Atlas fix plans."""

import pytest

from woodpecker.testing import make_atlas

from .helpers import assert_plan_check_fix_cycle, example_plan_path

pytest.importorskip("woodpecker_atlas_plugin")


def test_atlas_plan_checks_and_fixes_synthetic_dataset():
    dataset = make_atlas(missing=["project_id"])
    dataset["pr"].encoding["complevel"] = 5
    plan_path = example_plan_path("atlas_basic_plan.json")

    def assert_unchanged(ds):
        assert "project_id" not in ds.attrs
        assert ds["pr"].encoding["complevel"] == 5

    def assert_fixed(ds):
        assert ds.attrs["project_id"] == "c3s-ipcc-atlas"
        assert ds["pr"].encoding["complevel"] == 1
        assert ds["pr"].encoding["zlib"] is True
        assert ds["pr"].encoding["shuffle"] is True

    assert_plan_check_fix_cycle(
        plan_path,
        dataset,
        expected_fix_ids=(
            "atlas.encoding_cleanup",
            "atlas.project_id_normalization",
        ),
        expected_changed=2,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
