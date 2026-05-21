"""xMIP-derived fix namespace for Woodpecker."""

from .xmip_0001 import (  # noqa: F401
    BroadcastLonLatFix,
    ConvertBoundsToVerticesFix,
    ConvertVerticesToBoundsFix,
    DropHelperGridCoordsFix,
    FixKnownCmip6MetadataFix,
    MarkSpatialCoordsFix,
    NormalizeCoordinateUnitsFix,
    NormalizeLongitudeConventionFix,
    NormalizeLonLatBoundsFix,
    PromoteMissingDimensionCoordsFix,
    RenameCmip6AxesFix,
    ReplaceXYWithNominalLonLatFix,
    SortVertexOrderFix,
)
