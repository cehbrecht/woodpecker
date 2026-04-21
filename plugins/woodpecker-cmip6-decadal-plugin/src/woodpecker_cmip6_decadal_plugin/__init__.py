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
