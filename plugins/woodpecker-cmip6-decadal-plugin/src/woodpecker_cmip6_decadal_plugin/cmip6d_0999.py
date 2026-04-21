from __future__ import annotations

from woodpecker.fixes.registry import FixRegistry, GroupFix

from .cmip6d_0001 import DecadalTimeMetadataFix
from .cmip6d_0002 import DecadalCalendarNormalizationFix
from .cmip6d_0003 import DecadalRealizationVariableFix
from .cmip6d_0004 import DecadalCoordinatesEncodingCleanupFix
from .cmip6d_0005 import DecadalRealizationCommentNormalizationFix
from .cmip6d_0006 import DecadalRealizationDtypeNormalizationFix
from .cmip6d_0007 import DecadalFillValueEncodingCleanupFix
from .cmip6d_0008 import DecadalFurtherInfoUrlNormalizationFix
from .cmip6d_0009 import DecadalStartTokenNormalizationFix
from .cmip6d_0010 import DecadalRealizationLongNameNormalizationFix
from .cmip6d_0011 import DecadalRealizationIndexNormalizationFix
from .cmip6d_0012 import DecadalLeadtimeMetadataNormalizationFix
from .cmip6d_0013 import DecadalModelGlobalAttributesFix
from .cmip6d_0014 import DecadalReftimeCoordinateFix
from .cmip6d_0015 import DecadalLeadtimeCoordinateFix


@FixRegistry.register
class Cmip6DecadalFullFixSuiteFix(GroupFix):
    local_id = "0999"
    name = "CMIP6 Decadal: full fix suite"
    description = (
        "Applies all CMIP6-decadal fixes (DecadalTimeMetadataFix–DecadalLeadtimeCoordinateFix) in sequence: "
        "calendar, encoding, realization metadata, start-token normalisation, "
        "model-specific global attributes, and leadtime/reftime coordinates."
    )
    categories = ["metadata", "calendar", "encoding", "structure"]
    priority = 99
    dataset = "CMIP6-decadal"
    members = [
        DecadalTimeMetadataFix,
        DecadalCalendarNormalizationFix,
        DecadalRealizationVariableFix,
        DecadalCoordinatesEncodingCleanupFix,
        DecadalRealizationCommentNormalizationFix,
        DecadalRealizationDtypeNormalizationFix,
        DecadalFillValueEncodingCleanupFix,
        DecadalFurtherInfoUrlNormalizationFix,
        DecadalStartTokenNormalizationFix,
        DecadalRealizationLongNameNormalizationFix,
        DecadalRealizationIndexNormalizationFix,
        DecadalLeadtimeMetadataNormalizationFix,
        DecadalModelGlobalAttributesFix,
        DecadalReftimeCoordinateFix,
        DecadalLeadtimeCoordinateFix,
    ]
