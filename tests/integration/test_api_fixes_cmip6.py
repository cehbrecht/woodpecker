"""End-to-end public API examples for CMIP6 synthetic datasets."""

import numpy as np
import pytest

from woodpecker.testing import make_cmip6

from .helpers import (
    assert_check_fix_cycle,
    assert_fix_dry_run_reports_change,
    assert_fix_write_reports_change,
    assert_no_core_fixes_reported,
    check_finding_ids,
)

pytest.importorskip("woodpecker_cmip6_plugin")

CMIP6_SOURCE_NAME = "c3s-cmip6.member.tas.nc"


def _cmip6_dataset(**overrides):
    return make_cmip6(overrides={"source_name": CMIP6_SOURCE_NAME, **overrides})


def test_cmip6_tas_celsius_units_are_detected_and_fixed():
    dataset = make_cmip6(overrides={"units": "degC"})
    before = dataset["tas"].values.copy()

    def assert_unchanged(ds):
        assert ds["tas"].attrs["units"] == "degC"
        np.testing.assert_allclose(ds["tas"].values, before)

    def assert_fixed(ds):
        assert ds["tas"].attrs["units"] == "K"
        np.testing.assert_allclose(ds["tas"].values, before + 273.15, rtol=1e-6)

    assert_check_fix_cycle(
        dataset,
        "woodpecker.normalize_tas_units_to_kelvin",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_cmip6_dummy_placeholder_fix_is_detected_and_applied():
    dataset = _cmip6_dataset()

    assert check_finding_ids(dataset, "cmip6.dummy_placeholder") == {"cmip6.dummy_placeholder"}
    assert_fix_dry_run_reports_change(dataset, "cmip6.dummy_placeholder")
    assert "woodpecker_fix_cmip6_0001" not in dataset.attrs

    assert_fix_write_reports_change(dataset, "cmip6.dummy_placeholder")
    assert dataset.attrs["woodpecker_fix_cmip6_0001"] == "applied"


@pytest.mark.parametrize(
    "dataset",
    [
        make_cmip6(missing=["units"]),
        make_cmip6(rename_vars={"tas": "temperature"}),
    ],
)
def test_cmip6_metadata_only_corruption_does_not_trigger_core_fixes(dataset):
    assert_no_core_fixes_reported(dataset)
