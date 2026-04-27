from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from .base import DataInput
from .detect import detect_input


@dataclass
class DirectoryInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    def load(self) -> xr.Dataset:
        raise NotImplementedError("DirectoryInput does not load a single dataset; call expand().")

    def expand(self) -> list[DataInput]:
        inputs: list[DataInput] = []
        for path in sorted(self.source_path.rglob("*")):
            data_input = detect_input(path)
            if data_input is not None:
                inputs.append(data_input)
        return inputs
