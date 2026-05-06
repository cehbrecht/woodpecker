"""End-to-end public API examples for CMIP7 synthetic datasets."""

import pytest

from woodpecker.testing import make_cmip7

from .helpers import assert_check_fix_cycle

pytest.importorskip("woodpecker_cmip7_plugin")


def test_cmip7_missing_project_id_is_detected_and_fixed():
    dataset = make_cmip7(missing=["project_id"])

    def assert_fixed(ds):
        assert ds.attrs["project_id"] == "CMIP7"

    assert_check_fix_cycle(
        dataset,
        "cmip7.ensure_project_id_present",
        assert_fixed=assert_fixed,
    )


def test_cmip7_temp_variable_is_detected_and_renamed_to_tas():
    dataset = make_cmip7(rename_vars={"tas": "temp"})

    def assert_unchanged(ds):
        assert set(ds.data_vars) == {"temp"}

    def assert_fixed(ds):
        assert set(ds.data_vars) == {"tas"}

    assert_check_fix_cycle(
        dataset,
        "cmip7.rename_temp_variable_to_tas",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )
