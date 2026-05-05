"""End-to-end public API examples for CORDEX synthetic datasets."""

import numpy as np

from woodpecker.testing import make_cordex

from .helpers import assert_check_fix_cycle, assert_no_core_fixes_reported


def test_cordex_decreasing_latitude_is_detected_and_fixed():
    dataset = make_cordex().isel(lat=slice(None, None, -1))
    before_values = dataset["tasmax"].values.copy()

    def assert_unchanged(ds):
        assert float(ds["lat"].values[0]) > float(ds["lat"].values[-1])
        np.testing.assert_allclose(ds["tasmax"].values, before_values)

    def assert_fixed(ds):
        assert float(ds["lat"].values[0]) < float(ds["lat"].values[-1])
        np.testing.assert_allclose(ds["tasmax"].values, before_values[:, ::-1, :])

    assert_check_fix_cycle(
        dataset,
        "woodpecker.ensure_latitude_is_increasing",
        assert_unchanged=assert_unchanged,
        assert_fixed=assert_fixed,
    )


def test_cordex_metadata_only_corruption_does_not_trigger_core_fixes():
    dataset = make_cordex(missing=["domain_id", "driving_model_id"])

    assert_no_core_fixes_reported(dataset)
