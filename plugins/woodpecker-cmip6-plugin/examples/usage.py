import woodpecker_cmip6_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_cmip6

dataset = make_cmip6(overrides={"source_name": "c3s-cmip6.member.tas.nc"})
findings = woodpecker.check(dataset, fixes="cmip6.dummy_placeholder")

if findings:
    preview = woodpecker.fix(dataset, fixes=findings.fix_ids)
    result = woodpecker.fix(dataset, fixes=findings.fix_ids, dry_run=False)
    print(findings)
    print(preview)
    print(result)
