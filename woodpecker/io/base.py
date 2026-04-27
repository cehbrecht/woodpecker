from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import xarray as xr


@dataclass
class DataInput(ABC):
    """Abstract input wrapper that can load and optionally persist a dataset."""

    source_path: Path | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def load(self) -> xr.Dataset: ...

    def save(
        self,
        dataset: xr.Dataset,
        dry_run: bool = True,
        output_adapter: OutputAdapter | None = None,
    ) -> bool:
        return not dry_run

    def expand(self) -> list[DataInput]:
        return [self]

    @property
    def is_available(self) -> bool:
        return True

    @property
    def source_name(self) -> str:
        if self.source_path is not None:
            return self.source_path.name
        if self.name:
            return self.name
        return "<in-memory>"

    @property
    def reference(self) -> str:
        if self.source_path is not None:
            return str(self.source_path)
        return self.source_name


class OutputAdapter(ABC):
    """Abstract output strategy used to persist transformed datasets."""

    format_name: str = ""

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    def target_path(self, data_input: DataInput) -> Path: ...

    @abstractmethod
    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool: ...
