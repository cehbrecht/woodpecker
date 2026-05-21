import woodpecker_xmip_plugin  # noqa: F401

import woodpecker
from woodpecker.testing import make_cmip6

dataset = make_cmip6()
dataset = dataset.rename({"lon": "longitude", "lat": "latitude"})

findings = woodpecker.check(dataset, fixes="xmip.rename_cmip6_axes")
print(findings)

result = woodpecker.fix(dataset, fixes="xmip.rename_cmip6_axes", dry_run=False)
print(result)
print(dataset)
