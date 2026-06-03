import json
from pathlib import Path

from woodpecker.recipes.models import FixRef, Recipe
from woodpecker.ui.formatting import format_fix_stats, format_recipes


def test_format_recipes_text_uses_step_wording():
    recipes = [
        Recipe(id="tests.one", steps=[FixRef(id="woodpecker.one")]),
        Recipe(
            id="tests.two",
            steps=[FixRef(id="woodpecker.one"), FixRef(id="woodpecker.two")],
        ),
    ]

    assert format_recipes(recipes, "text") == "tests.one: 1 step\ntests.two: 2 steps"


def test_format_recipes_json_uses_model_payloads():
    recipe = Recipe(id="tests.one", steps=[FixRef(id="woodpecker.one")])

    payload = json.loads(format_recipes([recipe], "json"))

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


def test_format_fix_stats_json_includes_preview_entries():
    payload = json.loads(
        format_fix_stats(
            {
                "attempted": 1,
                "changed": 1,
                "persist_attempted": 0,
                "persisted": 0,
                "persist_failed": 0,
                "preview": [
                    {
                        "path": "cmip6_bad.nc",
                        "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                        "name": "Normalize units",
                        "changed": True,
                    }
                ],
            },
            fmt="json",
            dry_run=True,
            force_apply=False,
            resolved_output_format="auto",
            provenance=False,
            provenance_path=Path("woodpecker.prov.json"),
        )
    )

    assert payload["preview"][0]["path"] == "cmip6_bad.nc"
    assert payload["preview"][0]["changed"] is True


def test_format_fix_stats_text_includes_dry_run_preview():
    output = format_fix_stats(
        {
            "attempted": 1,
            "changed": 1,
            "persist_attempted": 0,
            "persisted": 0,
            "persist_failed": 0,
            "preview": [
                {
                    "path": "cmip6_bad.nc",
                    "fix_id": "woodpecker.normalize_tas_units_to_kelvin",
                    "name": "Normalize units",
                    "changed": True,
                }
            ],
        },
        fmt="text",
        dry_run=True,
        force_apply=False,
        resolved_output_format="auto",
        provenance=False,
        provenance_path=Path("woodpecker.prov.json"),
    )

    assert "Preview:" in output
    assert "cmip6_bad.nc: woodpecker.normalize_tas_units_to_kelvin" in output
    assert "would change" in output
