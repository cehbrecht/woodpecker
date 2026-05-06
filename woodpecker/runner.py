from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Iterable

from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.io import DataInput, get_output_adapter

if TYPE_CHECKING:
    from woodpecker.plans.models import FixPlan


def run_check(inputs: Iterable[DataInput], fixes: Iterable[Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for data_input in inputs:
        dataset = data_input.load()
        identity = resolve_dataset_identity(dataset)
        for fix in fixes:
            if not dataset_type_matches_declared(
                getattr(fix, "dataset", None), identity.dataset_type
            ):
                continue
            if not fix.matches(dataset):
                continue
            for message in fix.check(dataset):
                findings.append(
                    {
                        "path": data_input.reference,
                        "fix_id": getattr(fix, "id", ""),
                        "name": fix.name,
                        "message": message,
                    }
                )
        close = getattr(dataset, "close", None)
        if callable(close):
            close()
    return findings


def run_fix(
    inputs: Iterable[DataInput],
    fixes: Iterable[Any],
    dry_run: bool = True,
    force_apply: bool = False,
    output_format: str = "auto",
    embed_provenance_metadata: bool = False,
    provenance_run_id: str | None = None,
) -> dict[str, int]:
    changed = 0
    attempted = 0
    persist_attempted = 0
    persisted = 0
    persist_failed = 0
    output_adapter = get_output_adapter(output_format)
    for data_input in inputs:
        dataset = data_input.load()
        identity = resolve_dataset_identity(dataset)
        dataset_changed = False
        applied_fix_ids: list[str] = []
        for fix in fixes:
            fix_id = getattr(fix, "id", "")
            attempted_fix, changed_fix = apply_configured_fix(
                dataset,
                fix,
                dataset_type=identity.dataset_type,
                dry_run=dry_run,
                force_apply=force_apply,
                fix_id=fix_id,
            )
            if attempted_fix:
                attempted += 1
            if changed_fix:
                changed += 1
                dataset_changed = True
                applied_fix_ids.append(fix_id)
        if dataset_changed and not dry_run:
            if embed_provenance_metadata:
                dataset.attrs["woodpecker_provenance"] = json.dumps(
                    {
                        "run_id": provenance_run_id or "",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "source": data_input.reference,
                        "applied_fix_ids": applied_fix_ids,
                    },
                    sort_keys=True,
                )
            persist_attempted += 1
            if data_input.save(dataset, dry_run=False, output_adapter=output_adapter):
                persisted += 1
            else:
                persist_failed += 1
        close = getattr(dataset, "close", None)
        if callable(close):
            close()
    return {
        "attempted": attempted,
        "changed": changed,
        "persist_attempted": persist_attempted,
        "persisted": persisted,
        "persist_failed": persist_failed,
    }


def apply_configured_fix(
    dataset: Any,
    fix: Any,
    *,
    dataset_type: str | None,
    dry_run: bool,
    force_apply: bool,
    fix_id: str,
) -> tuple[bool, bool]:
    if not dataset_type_matches_declared(getattr(fix, "dataset", None), dataset_type):
        return False, False

    if not force_apply and not fix.matches(dataset):
        return False, False

    if not hasattr(fix, "apply"):
        raise TypeError(f"Fix '{fix_id}' does not implement apply()")

    return True, bool(fix.apply(dataset, dry_run=dry_run))


def _instantiate_fix(registry: Any, fix_id: str) -> Any:
    instantiate = getattr(registry, "instantiate", None)
    if not callable(instantiate):
        raise TypeError("Registry must provide instantiate(id)")
    return instantiate(fix_id)


def apply_fix_plan(ds: Any, plan: "FixPlan", registry: Any) -> Any:
    """Resolve plan fix identifiers and apply fixes in order."""

    identity = resolve_dataset_identity(ds)

    for ref in plan.steps:
        resolved_fix_id = plan.resolve_fix_identifier(ref)
        fix = _instantiate_fix(registry, resolved_fix_id)

        if hasattr(fix, "configure"):
            configured_fix = fix.configure(ref.options)
            if configured_fix is not None:
                fix = configured_fix

        apply_configured_fix(
            ds,
            fix,
            dataset_type=identity.dataset_type,
            dry_run=False,
            force_apply=False,
            fix_id=resolved_fix_id,
        )

    return ds
