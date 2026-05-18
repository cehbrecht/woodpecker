from __future__ import annotations

from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check, execute_fix
from woodpecker.results import CheckResult, FixResult


def _normalize_fixes(fixes: str | Sequence[str] | None) -> tuple[str, ...]:
    if fixes is None:
        return ()
    if isinstance(fixes, str):
        return (fixes,)
    return tuple(str(item) for item in fixes)


def check(
    inputs: Any,
    fixes: str | Sequence[str] | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    options: dict[str, dict[str, Any]] | None = None,
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs using directly selected fixes."""
    identifiers = _normalize_fixes(fixes)
    return CheckResult(
        findings=tuple(
            execute_check(
                inputs,
                dataset=dataset,
                categories=categories,
                identifiers=identifiers,
                fix_options=options,
                ordered_identifiers=identifiers,
                strict_io=strict_io,
            )
        )
    )


def fix(
    inputs: Any,
    fixes: str | Sequence[str] | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    dry_run: bool = True,
    output_format: str = "auto",
    options: dict[str, dict[str, Any]] | None = None,
    strict_io: bool = False,
) -> FixResult:
    """Apply directly selected fixes and return structured stats."""
    identifiers = _normalize_fixes(fixes)
    return FixResult(
        stats=execute_fix(
            inputs,
            dataset=dataset,
            categories=categories,
            identifiers=identifiers,
            write=not dry_run,
            output_format=output_format,
            fix_options=options,
            ordered_identifiers=identifiers,
            strict_io=strict_io,
        )
    )
