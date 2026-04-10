from __future__ import annotations

from ..registry import FixRegistry, GroupFix
from .cmip6d_0001 import CMIP6D_0001
from .cmip6d_0002 import CMIP6D_0002
from .cmip6d_0003 import CMIP6D_0003
from .cmip6d_0004 import CMIP6D_0004
from .cmip6d_0005 import CMIP6D_0005
from .cmip6d_0006 import CMIP6D_0006
from .cmip6d_0007 import CMIP6D_0007
from .cmip6d_0008 import CMIP6D_0008
from .cmip6d_0009 import CMIP6D_0009
from .cmip6d_0010 import CMIP6D_0010
from .cmip6d_0011 import CMIP6D_0011
from .cmip6d_0012 import CMIP6D_0012
from .cmip6d_0013 import CMIP6D_0013
from .cmip6d_0014 import CMIP6D_0014
from .cmip6d_0015 import CMIP6D_0015


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
