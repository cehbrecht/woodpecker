import json
from pathlib import Path

from woodpecker.fix_plans.models import FixPlan, FixRef
from woodpecker.ui.formatting import format_fix_stats, format_plans


def test_format_plans_text_uses_step_wording():
    plans = [
        FixPlan(id="tests.one", steps=[FixRef(id="woodpecker.one")]),
        FixPlan(
            id="tests.two",
            steps=[FixRef(id="woodpecker.one"), FixRef(id="woodpecker.two")],
        ),
    ]

    assert format_plans(plans, "text") == "tests.one: 1 step\ntests.two: 2 steps"


def test_format_plans_json_uses_model_payloads():
    plan = FixPlan(id="tests.one", steps=[FixRef(id="woodpecker.one")])

    payload = json.loads(format_plans([plan], "json"))

    assert payload[0]["id"] == "tests.one"
    assert payload[0]["steps"][0]["id"] == "woodpecker.one"


def test_format_fix_stats_json_includes_execution_context():
    payload = json.loads(
        format_fix_stats(
            {
                "attempted": 1,
                "changed": 1,
                "persist_attempted": 1,
                "persisted": 1,
                "persist_failed": 0,
            },
            fmt="json",
            dry_run=False,
            force_apply=True,
            resolved_output_format="netcdf",
            provenance=True,
            provenance_path=Path("woodpecker.prov.json"),
        )
    )

    assert payload["mode"] == "write"
    assert payload["force_apply"] is True
    assert payload["output_format"] == "netcdf"
    assert payload["provenance"] == "woodpecker.prov.json"
