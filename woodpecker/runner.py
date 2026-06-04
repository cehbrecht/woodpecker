from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Iterable, TypedDict

from woodpecker.fixes.labels import LabelRegistry
from woodpecker.identity import dataset_type_matches_declared, resolve_dataset_identity
from woodpecker.io import DataInput, get_output_adapter
from woodpecker.io.runtime import strict_io_mode

if TYPE_CHECKING:
    from woodpecker.recipes.models import Recipe


class FixPreview(TypedDict):
    """Per-input fix application preview emitted by run_fix."""

    path: str
    fix_id: str
    name: str
    labels: list[str]
    label_titles: list[str]
    label_metadata: list[dict[str, str]]
    changed: bool


class FixRunStats(TypedDict):
    """Structured stats emitted by run_fix."""

    attempted: int
    changed: int
    persist_attempted: int
    persisted: int
    persist_failed: int
    preview: list[FixPreview]


def run_check(
    inputs: Iterable[DataInput],
    fixes: Iterable[Any],
    *,
    strict_io: bool = False,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    with strict_io_mode(strict_io):
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
                    labels = _fix_labels(fix)
                    findings.append(
                        {
                            "path": data_input.reference,
                            "fix_id": getattr(fix, "id", ""),
                            "name": fix.name,
                            "labels": labels,
                            "label_titles": [LabelRegistry.title(label) for label in labels],
                            "label_metadata": [LabelRegistry.metadata(label) for label in labels],
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
    strict_io: bool = False,
) -> FixRunStats:
    changed = 0
    attempted = 0
    persist_attempted = 0
    persisted = 0
    persist_failed = 0
    preview: list[FixPreview] = []
    output_adapter = get_output_adapter(output_format)
    with strict_io_mode(strict_io):
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
                    labels = _fix_labels(fix)
                    preview.append(
                        {
                            "path": data_input.reference,
                            "fix_id": fix_id,
                            "name": getattr(fix, "name", ""),
                            "labels": labels,
                            "label_titles": [LabelRegistry.title(label) for label in labels],
                            "label_metadata": [LabelRegistry.metadata(label) for label in labels],
                            "changed": changed_fix,
                        }
                    )
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
        "preview": preview,
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
        raise TypeError(f"Fix function '{fix_id}' does not implement apply()")

    return True, bool(fix.apply(dataset, dry_run=dry_run))


def _fix_labels(fix: Any) -> list[str]:
    labels = getattr(fix, "labels", []) or []
    if not isinstance(labels, list):
        return []
    return [str(label) for label in labels]


def _instantiate_fix(registry: Any, fix_id: str) -> Any:
    instantiate = getattr(registry, "instantiate", None)
    if not callable(instantiate):
        raise TypeError("Registry must provide instantiate(id)")
    return instantiate(fix_id)


def apply_recipe(ds: Any, recipe: "Recipe", registry: Any) -> Any:
    """Resolve recipe fix identifiers and apply fixes in order."""

    identity = resolve_dataset_identity(ds)

    for ref in recipe.steps:
        resolved_fix_id = recipe.resolve_fix_identifier(ref)
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
