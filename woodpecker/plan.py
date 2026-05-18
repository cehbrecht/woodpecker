from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check_plan, execute_fix_plan
from woodpecker.results import CheckResult, FixResult


def check(
    plan_path: str | Path | None,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    plan_id: str | None = None,
    store_type: str = "json",
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs using a fix plan and return structured findings."""
    return CheckResult(
        findings=tuple(
            execute_check_plan(
                plan_path,
                inputs=inputs,
                dataset=dataset,
                categories=categories,
                identifiers=identifiers,
                plan_id=plan_id,
                store_type=store_type,
                strict_io=strict_io,
            )
        )
    )


def fix(
    plan_path: str | Path | None,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    plan_id: str | None = None,
    store_type: str = "json",
    strict_io: bool = False,
) -> FixResult:
    """Apply a fix plan and return structured stats."""
    return FixResult(
        stats=execute_fix_plan(
            plan_path,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            write=write,
            output_format=output_format,
            identifiers=identifiers,
            plan_id=plan_id,
            store_type=store_type,
            strict_io=strict_io,
        )
    )
