from __future__ import annotations

from typing import Any, Sequence

import woodpecker.fixes  # noqa: F401
from woodpecker.inout import normalize_inputs
from woodpecker.runner import run_check, run_fix, select_fixes


def check(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
    )
    return run_check(normalized, fixes)


def fix(
    inputs: Any,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    codes: Sequence[str] = (),
    write: bool = False,
    output_format: str = "auto",
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        codes=codes,
        strict_codes=True,
    )
    return run_fix(normalized, fixes, dry_run=not write, output_format=output_format)
