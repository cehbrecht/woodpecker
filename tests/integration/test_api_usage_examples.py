"""Minimal public API examples using synthetic climate datasets.

This file is intentionally light on test helpers. It shows the shape user code
should normally take: build or open a dataset, run ``woodpecker.check()``, run a
dry-run ``woodpecker.fix()``, apply with ``write=True``, and re-check.
"""

import numpy as np

import woodpecker
from woodpecker.testing import make_cmip6


def test_usage_example_check_and_fix_synthetic_cmip6_dataset():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()

    result = woodpecker.check(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
    )

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    dry_run = woodpecker.fix(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=False,
    )

    assert dry_run.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.fix(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
        write=True,
    )

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)

    assert not woodpecker.check(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
    ).has_findings
