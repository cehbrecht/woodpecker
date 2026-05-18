"""Minimal public API examples using synthetic climate datasets.

This file is intentionally light on test helpers. It shows the shape user code
should normally take: build or open a dataset, run ``woodpecker.check()``, run a
dry-run ``woodpecker.fix()``, apply with ``write=True``, and re-check. The plan
example shows the same flow through ``woodpecker.plan.check()`` and
``woodpecker.plan.fix()``.
"""

import numpy as np

import woodpecker
from woodpecker.fix_plans import DatasetMatcher, FixPlan, FixRef
from woodpecker.stores import AutoFixPlanStore, FixPlanCatalog, JsonFixPlanStore
from woodpecker.testing import integration_plan_path, make_cmip6


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

    assert not woodpecker.plan.check(
        None,
        inputs=dataset,
        store_type="auto",
        plan_id="woodpecker.normalize_tas_units_to_kelvin",
    ).has_findings

    assert not woodpecker.check(
        dataset,
        identifiers=["woodpecker.normalize_tas_units_to_kelvin"],
    ).has_findings


def test_usage_example_check_and_fix_synthetic_cmip6_dataset_with_plan():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()
    plan_path = integration_plan_path("cmip6_core_plan.yaml")

    result = woodpecker.plan.check(plan_path, inputs=dataset)

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    dry_run = woodpecker.plan.fix(
        plan_path,
        inputs=dataset,
        write=False,
    )

    assert dry_run.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.plan.fix(
        plan_path,
        inputs=dataset,
        write=True,
    )

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)

    assert not woodpecker.plan.check(plan_path, inputs=dataset).has_findings


def test_usage_example_check_and_fix_synthetic_cmip6_dataset_with_auto_plan():
    dataset = make_cmip6(overrides={"units": "degC"})
    original_values = dataset["tas"].values.copy()

    result = woodpecker.plan.check(
        None,
        inputs=dataset,
        store_type="auto",
        plan_id="woodpecker.normalize_tas_units_to_kelvin",
    )

    assert result.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)

    dry_run = woodpecker.plan.fix(
        None,
        inputs=dataset,
        store_type="auto",
        plan_id="woodpecker.normalize_tas_units_to_kelvin",
        write=False,
    )

    assert dry_run.changed == 1
    assert dataset["tas"].attrs["units"] == "degC"
    np.testing.assert_allclose(dataset["tas"].values, original_values)

    write = woodpecker.plan.fix(
        None,
        inputs=dataset,
        store_type="auto",
        plan_id="woodpecker.normalize_tas_units_to_kelvin",
        write=True,
    )

    assert write.changed == 1
    assert dataset["tas"].attrs["units"] == "K"
    np.testing.assert_allclose(dataset["tas"].values, original_values + 273.15)


def test_usage_example_query_fix_plan_catalog(tmp_path):
    dataset = make_cmip6(overrides={"units": "degC"})
    store = JsonFixPlanStore(tmp_path / "plans.yaml")
    store.save_plan(
        FixPlan(
            id="cmip6.curated_units",
            description="Curated CMIP6 units plan",
            match=DatasetMatcher(dataset_id_patterns=["CMIP6.CMIP.*.Amon.tas.*"]),
            steps=[FixRef(id="woodpecker.normalize_tas_units_to_kelvin")],
        )
    )
    catalog = FixPlanCatalog([store, AutoFixPlanStore()])

    matched_plans = catalog.lookup(dataset)

    assert [plan.id for plan in matched_plans] == [
        "cmip6.curated_units",
        "woodpecker.normalize_tas_units_to_kelvin",
    ]
