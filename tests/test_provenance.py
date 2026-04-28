from pathlib import Path
from types import SimpleNamespace

from woodpecker.provenance import format_provenance_source


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
