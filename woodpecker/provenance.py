from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable

from prov.model import ProvDocument

from woodpecker.io import DataInput, get_output_adapter
from woodpecker.io.runtime import warn_once


def format_provenance_source(
    context: Any,
    store_type: str,
    plan_location: Path | None,
) -> str | None:
    """Return a concise provenance source description for selected store input."""

    if context.source == "store":
        plan_ids = [selected.id for selected in context.selected_plans if selected.id]
        selected_text = ", ".join(plan_ids) if plan_ids else "<unnamed>"
        if plan_location is None:
            return f"store type={store_type} plans={selected_text}"
        return f"store type={store_type} location={plan_location} plans={selected_text}"

    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_prov_document(
    inputs: Iterable[DataInput],
    selected_fix_ids: list[str],
    selected_fixes: Iterable[Any] | None,
    selected_plans: Iterable[Any] | None,
    stats: dict[str, int],
    mode: str,
    output_format: str,
    plan: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id = run_id or f"woodpecker-run-{uuid.uuid4()}"
    generated_at = utc_now_iso()

    try:
        core_version = version("woodpecker")
    except PackageNotFoundError:
        core_version = "unknown"

    providers: list[dict[str, str]] = []
    seen_providers: set[str] = set()

    for selected_plan in list(selected_plans or []):
        runtime_metadata = getattr(selected_plan, "runtime_metadata", None)
        provider = getattr(runtime_metadata, "provider", None)
        provider_name = str(getattr(provider, "name", "") or "").strip()
        if not provider_name or provider_name in seen_providers:
            continue
        provider_version = str(getattr(provider, "version", "") or "").strip() or "unknown"
        providers.append({"name": provider_name, "version": provider_version})
        seen_providers.add(provider_name)

    plugin_versions: dict[str, str] = {}
    for fix in list(selected_fixes or []):
        module = getattr(type(fix), "__module__", "")
        package = module.split(".", 1)[0] if module else ""
        if not package or package.startswith("woodpecker"):
            continue
        if package in plugin_versions:
            continue
        try:
            plugin_versions[package] = version(package)
        except PackageNotFoundError:
            plugin_versions[package] = "unknown"

        if package not in seen_providers:
            providers.append({"name": package, "version": plugin_versions[package]})
            seen_providers.add(package)

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
        "selected_fix_ids": json.dumps(selected_fix_ids, sort_keys=True),
        "core_version": core_version,
        "plugin_versions": json.dumps(plugin_versions, sort_keys=True),
        "providers": json.dumps(providers, sort_keys=True),
        "stats": json.dumps(stats, sort_keys=True),
    }
    if plan:
        activity_attrs["plan"] = plan

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
            except (TypeError, ValueError) as exc:
                warn_once(
                    f"Failed to resolve output target reference for '{data_input.reference}': {exc}."
                )
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


def write_fix_provenance(
    context: Any,
    stats: dict[str, int],
    dry_run: bool,
    store_type: str,
    plan_location: Path | None,
    provenance_path: Path,
) -> None:
    """Write a provenance document for a check/fix run context."""

    provenance_source = format_provenance_source(context, store_type, plan_location)
    document = build_prov_document(
        inputs=context.inputs,
        selected_fix_ids=[getattr(fix, "id", "") for fix in context.fixes],
        selected_fixes=context.fixes,
        selected_plans=context.selected_plans,
        stats=stats,
        mode="dry-run" if dry_run else "write",
        output_format=context.resolved_output_format,
        plan=provenance_source,
    )
    write_prov_document(document, provenance_path)
