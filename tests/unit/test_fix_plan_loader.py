from __future__ import annotations

import json

import woodpecker
from woodpecker.fix_plans import FIX_PLAN_PATH_ENV, FixPlanLoader
from woodpecker.testing import make_cmip6


def test_fix_plan_loader_discovers_core_and_plugin_package_plans():
    plan_ids = {plan.id for plan in FixPlanLoader().catalog().list_plans()}

    assert "cmip6.core_units" in plan_ids
    assert "atlas.basic" in plan_ids
    assert "cmip6_decadal.full" in plan_ids
    assert "cmip7.esa_cci_water_vapour_zarr" in plan_ids
    assert "xmip.cmip6_preprocessing" in plan_ids


def test_fix_plan_loader_includes_explicit_directory_before_package_plans(tmp_path):
    (tmp_path / "plans.yaml").write_text(
        "plans:\n"
        "  - id: local.override\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    plans = FixPlanLoader().catalog(explicit_locations=[tmp_path]).list_plans()

    assert plans[0].id == "local.override"


def test_fix_plan_loader_includes_env_path(monkeypatch, tmp_path):
    path = tmp_path / "plans.json"
    path.write_text(
        json.dumps(
            {
                "plans": [
                    {
                        "id": "env.units",
                        "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(FIX_PLAN_PATH_ENV, str(path))

    plan_ids = {plan.id for plan in FixPlanLoader().catalog().list_plans()}

    assert "env.units" in plan_ids


def test_plan_api_resolves_discovered_plan_id_without_explicit_path():
    dataset = make_cmip6(overrides={"units": "degC"})

    findings = woodpecker.plan.check(dataset, None, plan_id="cmip6.core_units")

    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)


def test_plan_api_get_returns_plan_usable_by_check_and_fix():
    dataset = make_cmip6(overrides={"units": "degC"})
    plan = woodpecker.plan.get("cmip6.core_units")

    findings = woodpecker.plan.check(dataset, plan)
    preview = woodpecker.plan.fix(dataset, plan, dry_run=True)

    assert plan.id == "cmip6.core_units"
    assert findings.fix_ids == ("woodpecker.normalize_tas_units_to_kelvin",)
    assert preview.changed == 1


def test_plan_api_lists_discovered_plans():
    plan_ids = {plan.id for plan in woodpecker.plan.list_plans()}

    assert "cmip6.core_units" in plan_ids
    assert "xmip.cmip6_preprocessing" in plan_ids


def test_plan_api_catalog_selector_resolves_plugin_plan():
    dataset = make_cmip6(
        overrides={
            "source_id": "GFDL-CM4",
            "experiment_id": "historical",
        }
    )

    findings = woodpecker.plan.check(dataset, woodpecker.plan.catalog("xmip.cmip6_preprocessing"))

    assert "xmip.fix_known_cmip6_metadata" in findings.fix_ids
