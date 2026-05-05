"""End-to-end public API examples for Atlas synthetic datasets."""

from woodpecker.testing import make_atlas

from .helpers import assert_check_fix_cycle, assert_no_core_fixes_reported


def test_atlas_coordinate_fill_value_encoding_is_detected_and_fixed():
    dataset = make_atlas()
    dataset["time"].encoding["_FillValue"] = -9999

    def assert_unchanged(ds):
        assert ds["time"].encoding["_FillValue"] == -9999

    def assert_fixed(ds):
        assert "_FillValue" not in ds["time"].encoding

    assert_check_fix_cycle(
        dataset,
        "woodpecker.remove_coordinate_fill_value_encodings",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_atlas_encoding_cleanup_plugin_is_detected_and_fixed():
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


def test_atlas_project_id_normalization_plugin_is_detected_and_fixed():
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


def test_atlas_metadata_only_corruption_does_not_trigger_core_fixes():
    dataset = make_atlas(overrides={"project_id": "not-an-atlas-project"})

    assert_no_core_fixes_reported(dataset)
