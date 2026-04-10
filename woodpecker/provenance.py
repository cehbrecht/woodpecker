from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

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

    entities: dict[str, dict[str, Any]] = {}
    used: dict[str, dict[str, Any]] = {}

    for idx, data_input in enumerate(inputs):
        entity_id = f"entity:input:{idx}"
        target_reference = data_input.reference
        if output_adapter is not None and data_input.source_path is not None:
            try:
                target_reference = str(output_adapter.target_path(data_input))
            except Exception:
                target_reference = data_input.reference

        entities[entity_id] = {
            "prov:type": "prov:Entity",
            "reference": data_input.reference,
            "target_reference": target_reference,
        }
        used[f"used:{idx}"] = {
            "prov:activity": f"activity:{run_id}",
            "prov:entity": entity_id,
        }

    activity_attrs: dict[str, Any] = {
        "prov:type": "woodpecker:FixRun",
        "generatedAtTime": generated_at,
        "mode": mode,
        "output_format": output_format,
        "selected_codes": selected_codes,
        "stats": stats,
    }
    if workflow:
        activity_attrs["workflow"] = workflow

    return {
        "prefix": {
            "prov": "http://www.w3.org/ns/prov#",
            "woodpecker": "https://github.com/macpingu/woodpecker#",
        },
        "entity": entities,
        "activity": {
            f"activity:{run_id}": activity_attrs,
        },
        "agent": {
            "agent:woodpecker": {
                "prov:type": "prov:SoftwareAgent",
                "name": "woodpecker",
            }
        },
        "wasAssociatedWith": {
            f"association:{run_id}": {
                "prov:activity": f"activity:{run_id}",
                "prov:agent": "agent:woodpecker",
            }
        },
        "used": used,
    }


def write_prov_document(document: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
