from .base import DataInput, OutputAdapter
from .detect import collect_netcdf_files, detect_input_kind, detect_path_kind
from .folder import FolderInput
from .nc import NetCDFInput, NetCDFOutputAdapter
from .normalize import get_output_adapter, normalize_inputs
from .runtime import _netcdf_backend_available, _zarr_backend_available, get_io_availability
from .xr import XarrayInput
from .zarr import ZarrInput, ZarrOutputAdapter

__all__ = [
    "collect_netcdf_files",
    "DataInput",
    "detect_input_kind",
    "detect_path_kind",
    "FolderInput",
    "get_io_availability",
    "get_output_adapter",
    "NetCDFInput",
    "NetCDFOutputAdapter",
    "normalize_inputs",
    "OutputAdapter",
    "XarrayInput",
    "ZarrInput",
    "ZarrOutputAdapter",
    "_netcdf_backend_available",
    "_zarr_backend_available",
]
