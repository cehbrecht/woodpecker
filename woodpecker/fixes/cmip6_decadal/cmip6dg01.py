from __future__ import annotations

from ..registry import FixRegistry, GroupFix
from .cmip6d01 import CMIP6D_0001
from .cmip6d02 import CMIP6D_0002
from .cmip6d03 import CMIP6D_0003
from .cmip6d04 import CMIP6D_0004
from .cmip6d05 import CMIP6D_0005
from .cmip6d06 import CMIP6D_0006
from .cmip6d07 import CMIP6D_0007
from .cmip6d08 import CMIP6D_0008
from .cmip6d09 import CMIP6D_0009
from .cmip6d10 import CMIP6D_0010
from .cmip6d11 import CMIP6D_0011
from .cmip6d12 import CMIP6D_0012
from .cmip6d13 import CMIP6D_0013
from .cmip6d14 import CMIP6D_0014
from .cmip6d15 import CMIP6D_0015


@FixRegistry.register
class CMIP6DG_0001(GroupFix):
    code = "CMIP6DG_0001"
    name = "CMIP6 Decadal: full fix suite"
    description = (
        "Applies all CMIP6-decadal fixes (CMIP6D_0001–CMIP6D_0015) in sequence: "
        "calendar, encoding, realization metadata, start-token normalisation, "
        "model-specific global attributes, and leadtime/reftime coordinates."
    )
    categories = ["metadata", "calendar", "encoding", "structure"]
    priority = 99
    dataset = "CMIP6-decadal"
    members = [
        CMIP6D_0001,
        CMIP6D_0002,
        CMIP6D_0003,
        CMIP6D_0004,
        CMIP6D_0005,
        CMIP6D_0006,
        CMIP6D_0007,
        CMIP6D_0008,
        CMIP6D_0009,
        CMIP6D_0010,
        CMIP6D_0011,
        CMIP6D_0012,
        CMIP6D_0013,
        CMIP6D_0014,
        CMIP6D_0015,
    ]
