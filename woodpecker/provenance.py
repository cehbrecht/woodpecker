from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from prov.model import ProvDocument

from woodpecker.inout import DataInput, get_output_adapter


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_prov_document(
    inputs: Iterable[DataInput],
    selected_codes: list[str],
    stats: dict[str, int],
    mode: str,
    output_format: str,
    workflow: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id = run_id or f"woodpecker-run-{uuid.uuid4()}"
    generated_at = utc_now_iso()

    output_adapter = get_output_adapter(output_format)

    doc = ProvDocument()
    doc.set_default_namespace("urn:woodpecker:")
    doc.add_namespace("woodpecker", "https://github.com/macpingu/woodpecker#")

    activity_id = f"activity-{run_id}"
    activity_attrs: dict[str, Any] = {
        "prov:type": "woodpecker:FixRun",
        "generatedAtTime": generated_at,
        "mode": mode,
        "output_format": output_format,
        "selected_codes": json.dumps(selected_codes, sort_keys=True),
        "stats": json.dumps(stats, sort_keys=True),
    }
    if workflow:
        activity_attrs["workflow"] = workflow

    doc.activity(activity_id, None, None, activity_attrs)
    agent_id = "agent-woodpecker"
    doc.agent(
        agent_id,
        {
            "prov:type": "prov:SoftwareAgent",
            "name": "woodpecker",
        },
    )
    doc.wasAssociatedWith(activity_id, agent_id)

    for idx, data_input in enumerate(inputs):
        entity_id = f"entity-input-{idx}"
        target_reference = data_input.reference
        if output_adapter is not None and data_input.source_path is not None:
            try:
                target_reference = str(output_adapter.target_path(data_input))
            except Exception:
                target_reference = data_input.reference

        doc.entity(
            entity_id,
            {
                "prov:type": "prov:Entity",
                "reference": data_input.reference,
                "target_reference": target_reference,
            },
        )
        doc.used(activity_id, entity_id)

    return json.loads(doc.serialize(format="json"))


def write_prov_document(document: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
