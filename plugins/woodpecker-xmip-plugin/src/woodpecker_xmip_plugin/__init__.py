"""xMIP-derived fix namespace for Woodpecker."""

from .xmip_0001 import (  # noqa: F401
    BroadcastLonLat,
    ConvertBoundsToVertices,
    ConvertVerticesToBounds,
    DropHelperGridCoords,
    KnownCmip6Metadata,
    MarkSpatialCoords,
    NormalizeCoordinateUnits,
    NormalizeLonLatBounds,
    RenameCmip6Axes,
    ReplaceXYWithNominalLonLat,
    SortVertexOrder,
)
