from __future__ import annotations

from .registry import Fix, FixRegistry


@FixRegistry.register
class CMIP6D01(Fix):
    code = "CMIP6D01"
    name = "Decadal metadata baseline"
    description = "Fixes known CMIP6 decadal (CDS) metadata issues (baseline scaffolding)."
    categories = ["metadata"]
    priority = 10
    dataset = "CMIP6-decadal"


@FixRegistry.register
class ATLAS01(Fix):
    code = "ATLAS01"
    name = "ATLAS encoding cleanup"
    description = "Fixes common ATLAS encoding/deflation issues (baseline scaffolding)."
    categories = ["encoding", "metadata"]
    priority = 20
    dataset = "ATLAS"
