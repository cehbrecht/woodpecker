import woodpecker_atlas_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_atlas

dataset = make_atlas()
findings = woodpecker.check(
    dataset,
    fixes=[
        "atlas.encoding_cleanup",
        "atlas.project_id_normalization",
    ],
)

if findings:
    preview = woodpecker.fix(dataset, fixes=findings.fix_ids)
    result = woodpecker.fix(dataset, fixes=findings.fix_ids, dry_run=False)
    print(findings)
    print(preview)
    print(result)
