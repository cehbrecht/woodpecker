import woodpecker_xmip_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_cmip6

dataset = make_cmip6()
dataset = dataset.rename({"lon": "longitude", "lat": "latitude"})

findings = woodpecker.check(dataset, fixes="xmip.cmip6_preprocessing")
print(findings)

result = woodpecker.fix(dataset, fixes="xmip.cmip6_preprocessing", dry_run=False)
print(result)
print(dataset)
