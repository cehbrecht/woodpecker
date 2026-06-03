from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class CheckResult:
    """Structured result returned by ``woodpecker.check()``."""

    findings: tuple[Mapping[str, str], ...]

    def __bool__(self) -> bool:
        return self.count > 0

    def __len__(self) -> int:
        return self.count

    def __str__(self) -> str:
        if not self:
            return "No findings."
        fix_count = len(set(self.fix_ids))
        finding_label = "finding" if self.count == 1 else "findings"
        fix_label = "fix" if fix_count == 1 else "fixes"
        ids = ", ".join(self.fix_ids)
        return f"{self.count} {finding_label} from {fix_count} {fix_label}: {ids}"

    @property
    def count(self) -> int:
        return len(self.findings)

    @property
    def fix_ids(self) -> tuple[str, ...]:
        return tuple(finding.get("fix_id", "") for finding in self.findings)


@dataclass(frozen=True)
class FixResult:
    """Structured result returned by ``woodpecker.fix()``."""

    stats: Mapping[str, Any]

    def __bool__(self) -> bool:
        return self.changed > 0

    def __len__(self) -> int:
        return self.changed

    def __str__(self) -> str:
        change_label = "change" if self.changed == 1 else "changes"
        attempted_label = "attempt" if self.attempted == 1 else "attempts"
        persisted_label = "persisted"
        failed = f", {self.failed} failed" if self.failed else ""
        return (
            f"{self.changed} {change_label}, "
            f"{self.attempted} {attempted_label}, "
            f"{self.persisted} {persisted_label}{failed}"
        )

    @property
    def count(self) -> int:
        return self.changed

    @property
    def attempted(self) -> int:
        return self.stats.get("attempted", 0)

    @property
    def changed(self) -> int:
        return self.stats.get("changed", 0)

    @property
    def persist_attempted(self) -> int:
        return self.stats.get("persist_attempted", 0)

    @property
    def persisted(self) -> int:
        return self.stats.get("persisted", 0)

    @property
    def failed(self) -> int:
        return self.stats.get("persist_failed", 0)

    @property
    def preview(self) -> tuple[Mapping[str, Any], ...]:
        """Per-input fix applications reported by dry-run/write execution."""

        return tuple(self.stats.get("preview", ()))
