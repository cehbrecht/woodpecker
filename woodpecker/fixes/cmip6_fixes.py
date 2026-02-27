from __future__ import annotations

from pathlib import Path

from .registry import Fix, FixRegistry


@FixRegistry.register
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal metadata baseline"
    description = "Fixes known CMIP6 decadal (CDS) metadata issues (baseline scaffolding)."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() == ".nc" and "cmip6" in path.name.lower()

    def check(self, path: Path) -> list[str]:
        findings = []
        if "decadal" not in path.name.lower():
            findings.append("expected CMIP6 decadal filename hint ('decadal') is missing")
        return findings

    def apply(self, path: Path, dry_run: bool = True) -> bool:
        return False


@FixRegistry.register
class ATLAS01(Fix):
    code = "ATLAS01"
    name = "ATLAS encoding cleanup"
    description = "Fixes common ATLAS encoding/deflation issues (baseline scaffolding)."
    categories = ["encoding", "metadata"]
    priority = 20
    dataset = "ATLAS"

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() == ".nc" and "atlas" in path.name.lower()

    def check(self, path: Path) -> list[str]:
        findings = []
        if path.name.lower().endswith(".nc") and " " in path.name:
            findings.append("filename contains spaces; use underscores for stable downstream tooling")
        return findings

    def apply(self, path: Path, dry_run: bool = True) -> bool:
        return False
