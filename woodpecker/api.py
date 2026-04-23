from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import woodpecker.fixes  # noqa: F401
from woodpecker.execution import run_check, run_fix, select_fixes
from woodpecker.inout import normalize_inputs
from woodpecker.plans.resolver import resolve_plan_source, resolve_selection_inputs


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_check(normalized, fixes)


def fix(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_fix(normalized, fixes, dry_run=not write, output_format=output_format)


def check_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    plan_id: str | None = None,
) -> list[dict[str, str]]:
    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    _, _, plan_identifiers, plan_fix_options = resolve_plan_source(
        inputs=normalized,
        store_type="json",
        plan_location=Path(plan_path),
        plan_id=plan_id,
    )

    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=plan_identifiers,
            source_fix_options=plan_fix_options,
        )
    )

    resolved_dataset = dataset
    resolved_categories = categories

    return check(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        identifiers=resolved_identifiers,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )


def fix_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    plan_id: str | None = None,
) -> dict[str, int]:
    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    _, _, plan_identifiers, plan_fix_options = resolve_plan_source(
        inputs=normalized,
        store_type="json",
        plan_location=Path(plan_path),
        plan_id=plan_id,
    )

    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=plan_identifiers,
            source_fix_options=plan_fix_options,
        )
    )

    resolved_dataset = dataset
    resolved_categories = categories

    resolved_output = output_format

    return fix(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        identifiers=resolved_identifiers,
        write=write,
        output_format=resolved_output,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
    )
