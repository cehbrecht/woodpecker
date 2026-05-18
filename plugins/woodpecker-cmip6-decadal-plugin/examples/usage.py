import woodpecker_cmip6_decadal_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_cmip6_decadal

fixes = [
    "cmip6_decadal.time_metadata",
    "cmip6_decadal.calendar_normalization",
    "cmip6_decadal.realization_variable",
]

dataset = make_cmip6_decadal(overrides={"source_name": "c3s-cmip6-decadal.member.tos.nc"})
dataset["time"].attrs.pop("long_name", None)
findings = woodpecker.check(dataset, fixes=fixes)

if findings:
    preview = woodpecker.fix(dataset, fixes=findings.fix_ids)
    result = woodpecker.fix(dataset, fixes=findings.fix_ids, dry_run=False)
    print(findings)
    print(preview)
    print(result)
