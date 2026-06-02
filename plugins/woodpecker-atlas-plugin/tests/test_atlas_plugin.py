import woodpecker_atlas_plugin  # noqa: F401
from _atlas_helpers import assert_check_fix_cycle, assert_plan_check_fix_cycle

import woodpecker
from woodpecker.fixes.registry import FixFunctionRegistry
from woodpecker.testing import make_atlas

EXPECTED_FIX_IDS = {
    "atlas.encoding_cleanup",
    "atlas.project_id_normalization",
}
PLAN = woodpecker.recipe.get("atlas.basic")


def test_plugin_registers_expected_fixes():
    fix_ids = {fix.id for fix in FixFunctionRegistry.discover()}

    assert EXPECTED_FIX_IDS.issubset(fix_ids)


def test_plugin_fixes_work_with_public_api():
    import woodpecker

    dataset = make_atlas()
    findings = woodpecker.check(dataset, fixes=sorted(EXPECTED_FIX_IDS))

    assert findings
    assert set(findings.fix_ids).issubset(EXPECTED_FIX_IDS)


def test_atlas_encoding_cleanup_is_detected_and_fixed():
    dataset = make_atlas()
    dataset["pr"].encoding["complevel"] = 5

    def assert_unchanged(ds):
        assert ds["pr"].encoding["complevel"] == 5

    def assert_fixed(ds):
        assert ds["pr"].encoding["complevel"] == 1
        assert ds["pr"].encoding["zlib"] is True
        assert ds["pr"].encoding["shuffle"] is True

    assert_check_fix_cycle(
        dataset,
        "atlas.encoding_cleanup",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_atlas_project_id_normalization_is_detected_and_fixed():
    dataset = make_atlas(missing=["project_id"])

    def assert_unchanged(ds):
        assert "project_id" not in ds.attrs

    def assert_fixed(ds):
        assert ds.attrs["project_id"] == "c3s-ipcc-atlas"

    assert_check_fix_cycle(
        dataset,
        "atlas.project_id_normalization",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_atlas_plan_checks_and_fixes_synthetic_dataset():
    dataset = make_atlas(missing=["project_id"])
    dataset["pr"].encoding["complevel"] = 5

    def assert_unchanged(ds):
        assert "project_id" not in ds.attrs
        assert ds["pr"].encoding["complevel"] == 5

    def assert_fixed(ds):
        assert ds.attrs["project_id"] == "c3s-ipcc-atlas"
        assert ds["pr"].encoding["complevel"] == 1
        assert ds["pr"].encoding["zlib"] is True
        assert ds["pr"].encoding["shuffle"] is True

    assert_plan_check_fix_cycle(
        PLAN,
        dataset,
        expected_fix_ids=(
            "atlas.encoding_cleanup",
            "atlas.project_id_normalization",
        ),
        expected_changed=2,
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
