from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check_plan, execute_fix_plan
from woodpecker.results import CheckResult, FixResult


def _normalize_fixes(fixes: str | Sequence[str] | None) -> tuple[str, ...]:
    if fixes is None:
        return ()
    if isinstance(fixes, str):
        return (fixes,)
    return tuple(str(item) for item in fixes)


def check(
    inputs: Any,
    plan: str | Path | None,
    *,
    plan_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs using fixes selected from a fix plan."""
    return CheckResult(
        findings=tuple(
            execute_check_plan(
                plan,
                inputs=inputs,
                dataset=dataset,
                categories=categories,
                identifiers=_normalize_fixes(fixes),
                plan_id=plan_id,
                store_type=store_type,
                strict_io=strict_io,
            )
        )
    )


def fix(
    inputs: Any,
    plan: str | Path | None,
    *,
    plan_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    write: bool = False,
    output_format: str = "auto",
    strict_io: bool = False,
) -> FixResult:
    """Apply fixes selected from a fix plan."""
    return FixResult(
        stats=execute_fix_plan(
            plan,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            identifiers=_normalize_fixes(fixes),
            write=write,
            output_format=output_format,
            plan_id=plan_id,
            store_type=store_type,
            strict_io=strict_io,
        )
    )
