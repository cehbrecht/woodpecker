from __future__ import annotations

from typing import Any

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.results import CheckResult, FixResult
from woodpecker.sources import Fixes, Source


def check(
    inputs: Any,
    source: Source | None = None,
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs and return structured findings."""
    return (source or Fixes()).check(inputs, strict_io=strict_io)


def fix(
    inputs: Any,
    source: Source | None = None,
    write: bool = False,
    output_format: str = "auto",
    strict_io: bool = False,
) -> FixResult:
    """Apply selected fixes and return structured stats."""
    return (source or Fixes()).fix(
        inputs,
        write=write,
        output_format=output_format,
        strict_io=strict_io,
    )
