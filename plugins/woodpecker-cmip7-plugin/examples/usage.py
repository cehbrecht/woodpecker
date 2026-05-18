import woodpecker_cmip7_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_cmip7

fixes = [
    "cmip7.ensure_project_id_present",
    "cmip7.rename_temp_variable_to_tas",
]

dataset = make_cmip7(missing=["project_id"], rename_vars={"tas": "temp"})
findings = woodpecker.check(dataset, fixes=fixes)

if findings:
    preview = woodpecker.fix(dataset, fixes=findings.fix_ids)
    result = woodpecker.fix(dataset, fixes=findings.fix_ids, dry_run=False)
    print(findings)
    print(preview)
    print(result)
