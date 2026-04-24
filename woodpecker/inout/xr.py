from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import xarray as xr

from .base import DataInput


@dataclass
class XarrayInput(DataInput):
    payload: xr.Dataset | xr.DataArray | None = None

    def load(self) -> xr.Dataset:
        if self.payload is None:
            raise ValueError("XarrayInput payload is required")
        if isinstance(self.payload, xr.DataArray):
            return self.payload.to_dataset(name=self.payload.name or "value")
        return self.payload


# ---------------------------------------------------------------------------
# Backend plugin interface
# ---------------------------------------------------------------------------

BACKEND_NAME = "xarray"


def is_available() -> bool:
    return True


def can_open(source: Any) -> bool:
    return isinstance(source, (xr.Dataset, xr.DataArray))


def create_input(source: Any) -> XarrayInput:
    return XarrayInput(payload=source)


def create_output_adapter() -> None:
    return None
