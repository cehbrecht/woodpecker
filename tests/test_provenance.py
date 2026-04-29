import json
from pathlib import Path
from types import SimpleNamespace

from woodpecker.io.backends.xr import XarrayInput
from woodpecker.provenance import format_provenance_source, write_fix_provenance
from woodpecker.testing import make_cmip6


def test_format_provenance_source_for_store_mode():
    context = SimpleNamespace(
        source="store",
        selected_plans=[SimpleNamespace(id="alpha"), SimpleNamespace(id="beta")],
    )

    output = format_provenance_source(
        context,
        store_type="json",
        plan_location=Path("plans.json"),
    )

    assert output == "store type=json location=plans.json plans=alpha, beta"


def test_format_provenance_source_for_direct_mode():
    context = SimpleNamespace(source="direct", selected_plans=[])

    output = format_provenance_source(
        context,
        store_type="json",
        plan_location=Path("plans.json"),
    )

    assert output is None


def test_write_fix_provenance_writes_run_document(tmp_path: Path):
    fix = SimpleNamespace(canonical_id="woodpecker.example")
    plan = SimpleNamespace(id="woodpecker.plan")
    context = SimpleNamespace(
        source="store",
        inputs=[XarrayInput(payload=make_cmip6())],
        fixes=[fix],
        selected_plans=[plan],
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
        plan_location=Path("plans.json"),
        provenance_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    activity = next(iter(payload["activity"].values()))

    assert activity["mode"] == "dry-run"
    assert activity["output_format"] == "auto"
    assert activity["plan"] == "store type=json location=plans.json plans=woodpecker.plan"
    assert json.loads(activity["selected_fix_ids"]) == ["woodpecker.example"]
    assert json.loads(activity["stats"]) == stats
