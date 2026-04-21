"""CMIP6-decadal fix modules."""

from .cmip6d_0001 import DecadalTimeMetadataFix  # noqa: F401
from .cmip6d_0002 import DecadalCalendarNormalizationFix  # noqa: F401
from .cmip6d_0003 import DecadalRealizationVariableFix  # noqa: F401
from .cmip6d_0004 import DecadalCoordinatesEncodingCleanupFix  # noqa: F401
from .cmip6d_0005 import DecadalRealizationCommentNormalizationFix  # noqa: F401
from .cmip6d_0006 import DecadalRealizationDtypeNormalizationFix  # noqa: F401
from .cmip6d_0007 import DecadalFillValueEncodingCleanupFix  # noqa: F401
from .cmip6d_0008 import DecadalFurtherInfoUrlNormalizationFix  # noqa: F401
from .cmip6d_0009 import DecadalStartTokenNormalizationFix  # noqa: F401
from .cmip6d_0010 import DecadalRealizationLongNameNormalizationFix  # noqa: F401
from .cmip6d_0011 import DecadalRealizationIndexNormalizationFix  # noqa: F401
from .cmip6d_0012 import DecadalLeadtimeMetadataNormalizationFix  # noqa: F401
from .cmip6d_0013 import DecadalModelGlobalAttributesFix  # noqa: F401
from .cmip6d_0014 import DecadalReftimeCoordinateFix  # noqa: F401
from .cmip6d_0015 import DecadalLeadtimeCoordinateFix  # noqa: F401
from .cmip6d_0999 import Cmip6DecadalFullFixSuiteFix  # noqa: F401

# Backward-compatible exports
CMIP6D_0001 = DecadalTimeMetadataFix
CMIP6D_0002 = DecadalCalendarNormalizationFix
CMIP6D_0003 = DecadalRealizationVariableFix
CMIP6D_0004 = DecadalCoordinatesEncodingCleanupFix
CMIP6D_0005 = DecadalRealizationCommentNormalizationFix
CMIP6D_0006 = DecadalRealizationDtypeNormalizationFix
CMIP6D_0007 = DecadalFillValueEncodingCleanupFix
CMIP6D_0008 = DecadalFurtherInfoUrlNormalizationFix
CMIP6D_0009 = DecadalStartTokenNormalizationFix
CMIP6D_0010 = DecadalRealizationLongNameNormalizationFix
CMIP6D_0011 = DecadalRealizationIndexNormalizationFix
CMIP6D_0012 = DecadalLeadtimeMetadataNormalizationFix
CMIP6D_0013 = DecadalModelGlobalAttributesFix
CMIP6D_0014 = DecadalReftimeCoordinateFix
CMIP6D_0015 = DecadalLeadtimeCoordinateFix
CMIP6D_0999 = Cmip6DecadalFullFixSuiteFix
