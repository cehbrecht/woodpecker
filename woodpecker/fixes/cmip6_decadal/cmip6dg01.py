from __future__ import annotations

from ..registry import FixRegistry, GroupFix
from .cmip6d01 import CMIP6D01
from .cmip6d02 import CMIP6D02
from .cmip6d03 import CMIP6D03
from .cmip6d04 import CMIP6D04
from .cmip6d05 import CMIP6D05
from .cmip6d06 import CMIP6D06
from .cmip6d07 import CMIP6D07
from .cmip6d08 import CMIP6D08
from .cmip6d09 import CMIP6D09
from .cmip6d10 import CMIP6D10
from .cmip6d11 import CMIP6D11
from .cmip6d12 import CMIP6D12
from .cmip6d13 import CMIP6D13
from .cmip6d14 import CMIP6D14
from .cmip6d15 import CMIP6D15


@FixRegistry.register
class CMIP6DG01(GroupFix):
    code = "CMIP6DG01"
    name = "CMIP6 Decadal: full fix suite"
    description = (
        "Applies all CMIP6-decadal fixes (CMIP6D01–CMIP6D15) in sequence: "
        "calendar, encoding, realization metadata, start-token normalisation, "
        "model-specific global attributes, and leadtime/reftime coordinates."
    )
    categories = ["metadata", "calendar", "encoding", "structure"]
    priority = 99
    dataset = "CMIP6-decadal"
    members = [
        CMIP6D01, CMIP6D02, CMIP6D03, CMIP6D04, CMIP6D05,
        CMIP6D06, CMIP6D07, CMIP6D08, CMIP6D09, CMIP6D10,
        CMIP6D11, CMIP6D12, CMIP6D13, CMIP6D14, CMIP6D15,
    ]
