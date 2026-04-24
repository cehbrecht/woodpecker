from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from .base import DataInput
from .detect import collect_netcdf_files


@dataclass
class FolderInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    def load(self) -> xr.Dataset:
        raise NotImplementedError("FolderInput does not load a single dataset; call expand().")

    def expand(self) -> list[DataInput]:
        from .nc import NetCDFInput

        return [
            NetCDFInput(source_path=file_path, name=file_path.name)
            for file_path in collect_netcdf_files([self.source_path])
        ]
