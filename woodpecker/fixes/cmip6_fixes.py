from __future__ import annotations

from woodpecker.data_input import DataInput

from .registry import Fix, FixRegistry


def _lower_source_name(data_input: DataInput) -> str:
    return data_input.source_name.lower()


@FixRegistry.register
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal metadata baseline"
    description = "Fixes known CMIP6 decadal (CDS) metadata issues (baseline scaffolding)."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"

    def matches(self, data_input: DataInput) -> bool:
        source = _lower_source_name(data_input)
        return source.endswith(".nc") and "cmip6" in source

    def check(self, data_input: DataInput) -> list[str]:
        findings = []
        if "decadal" not in _lower_source_name(data_input):
            findings.append("expected CMIP6 decadal filename hint ('decadal') is missing")
        return findings

    def apply(self, data_input: DataInput, dry_run: bool = True) -> bool:
        if "decadal" in _lower_source_name(data_input):
            return False

        path = data_input.source_path
        if dry_run:
            return True

        if path is None:
            attrs = getattr(data_input.payload, "attrs", None)
            if isinstance(attrs, dict):
                attrs["woodpecker_fix_CMIP6D01"] = "applied"
            return True

        target = path.with_name(f"{path.stem}_decadal{path.suffix}")

        if target.exists():
            return False

        path.rename(target)
        return True


@FixRegistry.register
class ATLAS01(Fix):
    code = "ATLAS01"
    name = "ATLAS encoding cleanup"
    description = "Fixes common ATLAS encoding/deflation issues (baseline scaffolding)."
    categories = ["encoding", "metadata"]
    priority = 20
    dataset = "ATLAS"

    def matches(self, data_input: DataInput) -> bool:
        source = _lower_source_name(data_input)
        return source.endswith(".nc") and "atlas" in source

    def check(self, data_input: DataInput) -> list[str]:
        findings = []
        source_name = data_input.source_name
        if source_name.lower().endswith(".nc") and " " in source_name:
            findings.append(
                "filename contains spaces; use underscores for stable downstream tooling"
            )
        return findings

    def apply(self, data_input: DataInput, dry_run: bool = True) -> bool:
        source_name = data_input.source_name
        if " " not in source_name:
            return False

        path = data_input.source_path
        if dry_run:
            return True

        if path is None:
            attrs = getattr(data_input.payload, "attrs", None)
            if isinstance(attrs, dict):
                attrs["woodpecker_fix_ATLAS01"] = "applied"
            return True

        target = path.with_name(path.name.replace(" ", "_"))

        if target.exists():
            return False

        path.rename(target)
        return True
