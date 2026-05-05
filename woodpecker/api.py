from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check, execute_check_plan, execute_fix, execute_fix_plan
from woodpecker.results import CheckResult, FixResult


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> CheckResult:
    """Check inputs and return structured findings."""
    return CheckResult.from_findings(
        execute_check(
            inputs,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            fix_options=fix_options,
            ordered_identifiers=ordered_identifiers,
        )
    )


def fix(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> FixResult:
    """Apply selected fixes and return structured stats."""
    return FixResult.from_stats(
        execute_fix(
            inputs,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            write=write,
            output_format=output_format,
            fix_options=fix_options,
            ordered_identifiers=ordered_identifiers,
        )
    )


def check_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    plan_id: str | None = None,
) -> CheckResult:
    """Check inputs using a fix plan and return structured findings."""
    return CheckResult.from_findings(
        execute_check_plan(
            plan_path,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            plan_id=plan_id,
        )
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
) -> FixResult:
    """Apply a fix plan and return structured stats."""
    return FixResult.from_stats(
        execute_fix_plan(
            plan_path,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            write=write,
            output_format=output_format,
            identifiers=identifiers,
            plan_id=plan_id,
        )
    )
