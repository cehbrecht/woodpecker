import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from woodpecker.io import NetCDFInput
from woodpecker.io.backends.xr import XarrayInput
from woodpecker.provenance import format_provenance_source, write_fix_provenance
from woodpecker.testing import make_cmip6


@pytest.mark.parametrize(
    ("context", "store_type", "recipe_location", "expected"),
    [
        (
            SimpleNamespace(
                source="store",
                selected_recipes=[SimpleNamespace(id="alpha"), SimpleNamespace(id="beta")],
            ),
            "auto",
            None,
            "store type=auto recipes=alpha, beta",
        ),
        (
            SimpleNamespace(
                source="store",
                selected_recipes=[SimpleNamespace(id="alpha"), SimpleNamespace(id="beta")],
            ),
            "json",
            Path("recipes.json"),
            "store type=json location=recipes.json recipes=alpha, beta",
        ),
        (SimpleNamespace(source="direct", selected_recipes=[]), "json", Path("recipes.json"), None),
    ],
)
def test_format_provenance_source(context, store_type, recipe_location, expected):
    output = format_provenance_source(
        context,
        store_type=store_type,
        recipe_location=recipe_location,
    )

    assert output == expected


def test_write_fix_provenance_writes_run_document(tmp_path: Path):
    fix = SimpleNamespace(id="woodpecker.example")
    recipe = SimpleNamespace(id="woodpecker.recipe")
    context = SimpleNamespace(
        source="store",
        inputs=[XarrayInput(payload=make_cmip6())],
        fixes=[fix],
        selected_recipes=[recipe],
        resolved_output_format="auto",
    )
    stats = {
        "attempted": 1,
        "changed": 0,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }
    output_path = tmp_path / "woodpecker.prov.json"

    write_fix_provenance(
        context,
        stats,
        dry_run=True,
        store_type="json",
        recipe_location=Path("recipes.json"),
        provenance_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    activity = next(iter(payload["activity"].values()))

    assert activity["mode"] == "dry-run"
    assert activity["output_format"] == "auto"
    assert activity["recipe"] == "store type=json location=recipes.json recipes=woodpecker.recipe"
    assert json.loads(activity["selected_fix_ids"]) == ["woodpecker.example"]
    assert json.loads(activity["stats"]) == stats


def test_write_fix_provenance_warns_and_falls_back_on_invalid_target_reference(
    tmp_path: Path,
    monkeypatch,
):
    class BadAdapter:
        def target_path(self, data_input):
            _ = data_input
            raise ValueError("bad output target")

    monkeypatch.setattr(
        "woodpecker.provenance.get_output_adapter", lambda output_format: BadAdapter()
    )

    fix = SimpleNamespace(id="woodpecker.example")
    context = SimpleNamespace(
        source="store",
        inputs=[NetCDFInput(source_path=Path("cmip6_case.nc"), name="cmip6_case.nc")],
        fixes=[fix],
        selected_recipes=[],
        resolved_output_format="netcdf",
    )
    stats = {
        "attempted": 1,
        "changed": 0,
        "persist_attempted": 0,
        "persisted": 0,
        "persist_failed": 0,
    }
    output_path = tmp_path / "woodpecker.prov.json"

    with pytest.warns(UserWarning, match="Failed to resolve output target reference"):
        write_fix_provenance(
            context,
            stats,
            dry_run=True,
            store_type="json",
            recipe_location=None,
            provenance_path=output_path,
        )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    entity = next(iter(payload["entity"].values()))
    assert entity["reference"] == "cmip6_case.nc"
    assert entity["target_reference"] == "cmip6_case.nc"
