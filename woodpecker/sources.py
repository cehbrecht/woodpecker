from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Sequence

from woodpecker.commands import execute_check, execute_check_plan, execute_fix, execute_fix_plan
from woodpecker.results import CheckResult, FixResult


class Source(Protocol):
    """Selection source used by the public ``check`` and ``fix`` API."""

    def check(self, inputs: Any, *, strict_io: bool) -> CheckResult:
        """Check inputs with this source's fix selection."""
        ...

    def fix(
        self,
        inputs: Any,
        *,
        write: bool,
        output_format: str,
        strict_io: bool,
    ) -> FixResult:
        """Apply fixes selected by this source."""
        ...


def _normalize_identifiers(identifiers: str | Sequence[str] | None) -> tuple[str, ...]:
    if identifiers is None:
        return ()
    if isinstance(identifiers, str):
        return (identifiers,)
    return tuple(str(item) for item in identifiers)


@dataclass(frozen=True)
class Fixes:
    """Public source for selecting executable fixes directly."""

    identifiers: tuple[str, ...] = ()
    dataset: str | None = None
    categories: tuple[str, ...] = ()
    options: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __init__(
        self,
        identifiers: str | Sequence[str] | None = None,
        *,
        dataset: str | None = None,
        categories: Sequence[str] = (),
        options: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        object.__setattr__(self, "identifiers", _normalize_identifiers(identifiers))
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "categories", tuple(categories))
        object.__setattr__(self, "options", dict(options or {}))

    def check(self, inputs: Any, *, strict_io: bool) -> CheckResult:
        return CheckResult(
            findings=tuple(
                execute_check(
                    inputs,
                    dataset=self.dataset,
                    categories=self.categories,
                    identifiers=self.identifiers,
                    fix_options=self.options,
                    ordered_identifiers=self.identifiers,
                    strict_io=strict_io,
                )
            )
        )

    def fix(
        self,
        inputs: Any,
        *,
        write: bool,
        output_format: str,
        strict_io: bool,
    ) -> FixResult:
        return FixResult(
            stats=execute_fix(
                inputs,
                dataset=self.dataset,
                categories=self.categories,
                identifiers=self.identifiers,
                write=write,
                output_format=output_format,
                fix_options=self.options,
                ordered_identifiers=self.identifiers,
                strict_io=strict_io,
            )
        )


@dataclass(frozen=True)
class FixPlan:
    """Public source for selecting fixes through a fix-plan store."""

    plan: str | Path | None
    plan_id: str | None = None
    store_type: str = "json"
    dataset: str | None = None
    categories: tuple[str, ...] = ()
    identifiers: tuple[str, ...] = ()

    def __init__(
        self,
        plan: str | Path | None,
        *,
        plan_id: str | None = None,
        store_type: str = "json",
        dataset: str | None = None,
        categories: Sequence[str] = (),
        identifiers: str | Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "plan", plan)
        object.__setattr__(self, "plan_id", plan_id)
        object.__setattr__(self, "store_type", store_type)
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "categories", tuple(categories))
        object.__setattr__(self, "identifiers", _normalize_identifiers(identifiers))

    @classmethod
    def auto(cls, plan_id: str | None = None) -> FixPlan:
        """Select generated one-step plans from registered fixes."""
        return cls(None, plan_id=plan_id, store_type="auto")

    def check(self, inputs: Any, *, strict_io: bool) -> CheckResult:
        return CheckResult(
            findings=tuple(
                execute_check_plan(
                    self.plan,
                    inputs=inputs,
                    dataset=self.dataset,
                    categories=self.categories,
                    identifiers=self.identifiers,
                    plan_id=self.plan_id,
                    store_type=self.store_type,
                    strict_io=strict_io,
                )
            )
        )

    def fix(
        self,
        inputs: Any,
        *,
        write: bool,
        output_format: str,
        strict_io: bool,
    ) -> FixResult:
        return FixResult(
            stats=execute_fix_plan(
                self.plan,
                inputs=inputs,
                dataset=self.dataset,
                categories=self.categories,
                identifiers=self.identifiers,
                write=write,
                output_format=output_format,
                plan_id=self.plan_id,
                store_type=self.store_type,
                strict_io=strict_io,
            )
        )
