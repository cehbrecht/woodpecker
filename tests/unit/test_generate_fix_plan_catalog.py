import importlib.util
import json
from pathlib import Path

import pytest


def _load_generator_module():
    module_path = Path(__file__).parents[2] / "scripts" / "generate_fix_plan_catalog.py"
    spec = importlib.util.spec_from_file_location("generate_fix_plan_catalog", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_fix_plan_catalog_loads_single_yaml_plan_source(tmp_path):
    generator = _load_generator_module()
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir()

    (plan_dir / "cmip6_core_plan.yaml").write_text(
        "plans:\n"
        "  - id: cmip6.core_units\n"
        "    match:\n"
        "      attrs:\n"
        "        project_id: CMIP6\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    md_path = tmp_path / "FIX_PLANS.md"
    json_path = tmp_path / "FIX_PLANS.json"
    generator.generate_fix_plan_catalog(
        md_path=str(md_path),
        json_path=str(json_path),
        plan_dir=str(plan_dir),
        include_plugin_plans=False,
    )

    catalog = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert [item["id"] for item in catalog] == ["cmip6.core_units"]
    assert catalog[0]["source"] == "integration-tests"
    assert catalog[0]["source_files"] == [(plan_dir / "cmip6_core_plan.yaml").as_posix()]
    assert (
        f"[{(plan_dir / 'cmip6_core_plan.yaml').as_posix()}]"
        f"(https://github.com/cehbrecht/woodpecker/blob/main/"
        f"{(plan_dir / 'cmip6_core_plan.yaml').as_posix()})"
    ) in markdown
    assert "woodpecker.normalize_tas_units_to_kelvin" in markdown


def test_generate_fix_plan_catalog_rejects_duplicate_plan_ids(tmp_path):
    generator = _load_generator_module()
    plan_dir = tmp_path / "plans"
    plan_dir.mkdir()

    json_payload = {
        "plans": [
            {
                "id": "cmip6.core_units",
                "match": {"attrs": {"project_id": "CMIP6"}},
                "steps": [{"id": "woodpecker.normalize_tas_units_to_kelvin"}],
            }
        ]
    }
    (plan_dir / "cmip6_core_plan.json").write_text(json.dumps(json_payload), encoding="utf-8")
    (plan_dir / "cmip6_core_plan.yaml").write_text(
        "plans:\n"
        "  - id: cmip6.core_units\n"
        "    match:\n"
        "      attrs:\n"
        "        project_id: CMIP6\n"
        "    steps:\n"
        "      - id: woodpecker.normalize_tas_units_to_kelvin\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate definition for plan id 'cmip6.core_units'"):
        generator.load_integration_plans(plan_dir)


def test_generate_fix_plan_catalog_can_load_plugin_plan_sources():
    generator = _load_generator_module()

    plans = generator.load_plugin_plans()
    plan_by_id = {plan.id: (plan, source_files, source) for plan, source_files, source in plans}

    assert "xmip.cmip6_preprocessing" in plan_by_id
    plan, source_files, source = plan_by_id["xmip.cmip6_preprocessing"]
    assert source == "plugin:woodpecker_xmip_plugin"
    assert source_files == [
        "plugins/woodpecker-xmip-plugin/src/woodpecker_xmip_plugin/plans/cmip6_preprocessing.yaml"
    ]
    assert "xmip.normalize_coordinate_units" in [step.id for step in plan.steps]
