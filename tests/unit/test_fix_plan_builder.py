import json

import yaml

from woodpecker.fix_plans import document, fix, match, plan
from woodpecker.fix_plans.builder import FixPlanBuilder, FixPlanDocumentBuilder, FixStepBuilder
from woodpecker.fix_plans.models import FixPlan, FixPlanDocument


def test_fix_step_builder_creates_fix_ref_with_options_and_links():
    step = fix(
        "woodpecker.convert_units",
        {"units": {"tas": "K"}},
        dry_run_only=False,
        links=({"rel": "docs", "href": "https://example.invalid"},),
    )

    ref = step.to_model()

    assert isinstance(step, FixStepBuilder)
    assert ref.id == "woodpecker.convert_units"
    assert ref.options == {"units": {"tas": "K"}, "dry_run_only": False}
    assert ref.links[0].rel == "docs"


def test_plan_builder_creates_existing_fix_plan_model():
    built = plan(
        "cmip6.core_units",
        fix("woodpecker.normalize_tas_units_to_kelvin"),
        description="Core units plan",
    ).match(
        attrs={"project_id": "CMIP6"},
        dataset_id_patterns=["CMIP6.CMIP.*.Amon.tas.*"],
    )

    model = built.to_model()

    assert isinstance(built, FixPlanBuilder)
    assert isinstance(model, FixPlan)
    assert model.id == "cmip6.core_units"
    assert model.description == "Core units plan"
    assert model.match is not None
    assert model.match.attrs == {"project_id": "CMIP6"}
    assert model.steps[0].id == "woodpecker.normalize_tas_units_to_kelvin"


def test_plan_builder_scopes_local_fix_ids_to_plan_prefix():
    model = plan("atlas.basic", "encoding_cleanup").to_model()

    assert model.steps[0].id == "atlas.encoding_cleanup"


def test_plan_builder_accepts_match_builder_and_step_mappings():
    model = plan(
        "atlas.basic",
        {"id": "encoding_cleanup", "options": {"mode": "strict"}},
        match=match(path_patterns=["*atlas*.nc"]),
    ).to_model()

    assert model.match is not None
    assert model.match.path_patterns == ["*atlas*.nc"]
    assert model.steps[0].id == "atlas.encoding_cleanup"
    assert model.steps[0].options == {"mode": "strict"}


def test_plan_builder_serializes_as_fix_plan_document_json_and_yaml(tmp_path):
    built = plan("atlas.basic", fix("encoding_cleanup", mode="strict"))
    json_path = tmp_path / "plan.json"
    yaml_path = tmp_path / "plan.yaml"

    json_text = built.to_json(json_path)
    yaml_text = built.to_yaml(yaml_path)

    json_payload = json.loads(json_text)
    yaml_payload = yaml.safe_load(yaml_text)

    assert json_payload == yaml_payload
    assert json_payload["plans"][0]["id"] == "atlas.basic"
    assert json_payload["plans"][0]["steps"][0]["id"] == "atlas.encoding_cleanup"
    assert json_path.read_text(encoding="utf-8") == json_text
    assert yaml.safe_load(yaml_path.read_text(encoding="utf-8")) == yaml_payload


def test_document_builder_combines_multiple_python_plans():
    built = document(
        plan("atlas.basic", "encoding_cleanup"),
        plan("cmip6.core_units", "woodpecker.normalize_tas_units_to_kelvin"),
    )

    model = built.to_model()

    assert isinstance(built, FixPlanDocumentBuilder)
    assert isinstance(model, FixPlanDocument)
    assert [plan.id for plan in model.plans] == ["atlas.basic", "cmip6.core_units"]
    assert json.loads(built.to_json())["plans"][1]["id"] == "cmip6.core_units"
