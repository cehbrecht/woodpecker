from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check, execute_check_plan, execute_fix, execute_fix_plan


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
) -> list[dict[str, str]]:
    return execute_check(
        inputs,
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
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
) -> dict[str, int]:
    return execute_fix(
        inputs,
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        write=write,
        output_format=output_format,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )


def check_plan(
    plan_path: str | Path,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    plan_id: str | None = None,
) -> list[dict[str, str]]:
    return execute_check_plan(
        plan_path,
        inputs=inputs,
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        plan_id=plan_id,
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
    return execute_fix_plan(
        plan_path,
        inputs=inputs,
        dataset=dataset,
        categories=categories,
        write=write,
        output_format=output_format,
        identifiers=identifiers,
        plan_id=plan_id,
    )
