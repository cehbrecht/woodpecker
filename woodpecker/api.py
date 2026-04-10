from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import woodpecker.fixes  # noqa: F401
from woodpecker.inout import normalize_inputs
from woodpecker.runner import run_check, run_fix, select_fixes
from woodpecker.workflow import load_workflow


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_codes: Sequence[str] = (),
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
        fix_options=fix_options,
        ordered_codes=ordered_codes,
    )
    return run_check(normalized, fixes)


def fix(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_codes: Sequence[str] = (),
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
        fix_options=fix_options,
        ordered_codes=ordered_codes,
    )
    return run_fix(normalized, fixes, dry_run=not write, output_format=output_format)


def check_workflow(
    workflow_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
) -> list[dict[str, str]]:
    workflow_spec = load_workflow(Path(workflow_path))
    resolved_inputs = inputs if inputs is not None else workflow_spec.inputs
    normalized = normalize_inputs(resolved_inputs)
    resolution = workflow_spec.resolve([item.reference for item in normalized])

    resolved_dataset = dataset or resolution.dataset
    resolved_categories = categories or tuple(resolution.categories)
    resolved_codes = codes or tuple(resolution.codes)
    resolved_fix_options = resolution.fixes
    resolved_ordered_codes = (
        tuple(code.strip().upper() for code in codes if code.strip())
        if codes
        else tuple(resolution.ordered_codes)
    )
    return check(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )


def fix_workflow(
    workflow_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
) -> dict[str, int]:
    workflow_spec = load_workflow(Path(workflow_path))
    resolved_inputs = inputs if inputs is not None else workflow_spec.inputs
    normalized = normalize_inputs(resolved_inputs)
    resolution = workflow_spec.resolve([item.reference for item in normalized])

    resolved_dataset = dataset or resolution.dataset
    resolved_categories = categories or tuple(resolution.categories)
    resolved_codes = codes or tuple(resolution.codes)
    resolved_fix_options = resolution.fixes
    resolved_ordered_codes = (
        tuple(code.strip().upper() for code in codes if code.strip())
        if codes
        else tuple(resolution.ordered_codes)
    )
    resolved_output = (
        resolution.output_format
        if output_format == "auto" and resolution.output_format
        else output_format
    )
    return fix(
        normalized,
        dataset=resolved_dataset,
        categories=resolved_categories,
        codes=resolved_codes,
        write=write,
        output_format=resolved_output,
        fix_options=resolved_fix_options,
        ordered_codes=resolved_ordered_codes,
    )
