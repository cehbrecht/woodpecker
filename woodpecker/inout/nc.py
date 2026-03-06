from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from .base import DataInput, OutputAdapter, _netcdf_backend_available


@dataclass
class PathInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    @property
    def is_available(self) -> bool:
        return _netcdf_backend_available()

    def load(self) -> xr.Dataset:
        if not self.is_available:
            warnings.warn(
                f"NetCDF input backend unavailable for '{self.reference}'. Falling back to empty dataset.",
                stacklevel=2,
            )
            dataset = xr.Dataset()
            dataset.attrs.setdefault("source_name", self.source_name)
            return dataset
        try:
            dataset = xr.open_dataset(self.source_path)
        except Exception as exc:
            warnings.warn(
                f"Failed to read NetCDF input '{self.reference}': {exc}. Falling back to empty dataset.",
                stacklevel=2,
            )
            dataset = xr.Dataset()
        dataset.attrs.setdefault("source_name", self.source_name)
        return dataset

    def save(
        self,
        dataset: xr.Dataset,
        dry_run: bool = True,
        output_adapter: OutputAdapter | None = None,
    ) -> bool:
        if output_adapter is not None:
            return output_adapter.save(dataset, self, dry_run=dry_run)
        if dry_run:
            return False
        if not self.is_available:
            warnings.warn(
                f"NetCDF output backend unavailable for '{self.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        try:
            dataset.to_netcdf(self.source_path)
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write NetCDF output '{self.reference}': {exc}.",
                stacklevel=2,
            )
            return False


class NetCDFOutputAdapter(OutputAdapter):
    format_name = "netcdf"

    @property
    def is_available(self) -> bool:
        return _netcdf_backend_available()

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("NetCDF output requires a path-based input")
        return data_input.source_path.with_suffix(".nc")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        if not self.is_available:
            warnings.warn(
                f"NetCDF output backend unavailable for '{data_input.reference}'. Skipping write.",
                stacklevel=2,
            )
            return False
        target = self.target_path(data_input)
        try:
            dataset.to_netcdf(target)
            return True
        except Exception as exc:
            warnings.warn(
                f"Failed to write NetCDF output '{target}': {exc}.",
                stacklevel=2,
            )
            return False
