from __future__ import annotations

from dataclasses import dataclass

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
