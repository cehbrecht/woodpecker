from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import xarray as xr

from .base import DataInput


@dataclass
class XarrayInput(DataInput):
    payload: xr.Dataset | xr.DataArray | None = None

    @property
    def source_name(self) -> str:
        if self.name:
            return self.name
        if self.payload is not None:
            attrs = getattr(self.payload, "attrs", {})
            for key in ("source_name", "name", "id"):
                value = attrs.get(key)
                if isinstance(value, str) and value:
                    return value
            payload_name = getattr(self.payload, "name", None)
            if isinstance(payload_name, str) and payload_name:
                return payload_name
        return "<in-memory>"

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
