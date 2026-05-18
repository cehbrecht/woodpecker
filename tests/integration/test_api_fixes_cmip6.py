"""End-to-end public API examples for CMIP6 synthetic datasets."""

import numpy as np
import pytest

from woodpecker.testing import make_cmip6

from .helpers import (
    assert_check_fix_cycle,
    assert_no_core_fixes_reported,
)


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


@pytest.mark.parametrize(
    "dataset",
    [
        make_cmip6(missing=["units"]),
        make_cmip6(rename_vars={"tas": "temperature"}),
    ],
)
def test_cmip6_metadata_only_corruption_does_not_trigger_core_fixes(dataset):
    assert_no_core_fixes_reported(dataset)
