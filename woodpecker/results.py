from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CheckResult:
    """Structured result returned by ``woodpecker.check()``."""

    findings: tuple[Mapping[str, str], ...]

    @property
    def fix_ids(self) -> tuple[str, ...]:
        return tuple(finding.get("fix_id", "") for finding in self.findings)

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)


@dataclass(frozen=True)
class FixResult:
    """Structured result returned by ``woodpecker.fix()``."""

    stats: Mapping[str, int]

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
    def persist_failed(self) -> int:
        return self.stats.get("persist_failed", 0)

    @property
    def has_changes(self) -> bool:
        return self.changed > 0
