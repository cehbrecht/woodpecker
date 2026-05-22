"""xMIP-derived fix namespace for Woodpecker."""

from .xmip_0001 import (  # noqa: F401
    BroadcastLonLatFix,
    ConvertBoundsToVerticesFix,
    ConvertVerticesToBoundsFix,
    DropHelperGridCoordsFix,
    FixKnownCmip6MetadataFix,
    MarkSpatialCoordsFix,
    NormalizeCoordinateUnitsFix,
    NormalizeLonLatBoundsFix,
    RenameCmip6AxesFix,
    ReplaceXYWithNominalLonLatFix,
    SortVertexOrderFix,
)
