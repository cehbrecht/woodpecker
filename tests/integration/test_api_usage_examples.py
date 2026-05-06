"""Minimal public API examples using synthetic climate datasets.

This file is intentionally light on test helpers. It shows the shape user code
should normally take: build or open a dataset, run ``woodpecker.check()``, run a
dry-run ``woodpecker.fix()``, apply with ``write=True``, and re-check. The plan
example shows the same flow through ``woodpecker.check_plan()`` and
``woodpecker.fix_plan()``.
"""

from pathlib import Path

import numpy as np

import woodpecker
from woodpecker.testing import make_cmip6

PLAN_DIR = Path(__file__).resolve().parent / "plans"


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


def test_usage_example_check_and_fix_synthetic_cmip6_dataset_with_plan():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()
    plan_path = PLAN_DIR / "cmip6_core_plan.json"

    result = woodpecker.check_plan(plan_path, inputs=dataset)

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    dry_run = woodpecker.fix_plan(
        plan_path,
        inputs=dataset,
        write=False,
    )

    assert dry_run.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.fix_plan(
        plan_path,
        inputs=dataset,
        write=True,
    )

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)

    assert not woodpecker.check_plan(plan_path, inputs=dataset).has_findings
