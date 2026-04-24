from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any

import xarray as xr

from ..base import DataInput, OutputAdapter
from ..runtime import module_available, warn_once


def zarr_backend_available() -> bool:
    return all(module_available(name) for name in ("zarr", "numcodecs"))


def _fallback_dataset(source_name: str) -> xr.Dataset:
    dataset = xr.Dataset()
    dataset.attrs.setdefault("source_name", source_name)
    dataset.attrs["_woodpecker_load_failed"] = True
    return dataset


def _write_zarr(dataset: xr.Dataset, target: Path, reference: str) -> bool:
    try:
        dataset.to_zarr(target, mode="w")
        return True
    except Exception as exc:
        warn_once(f"Failed to write Zarr output '{reference}': {exc}.")
        return False


@dataclass
class ZarrInput(DataInput):
    source_path: Path

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)
        if not self.name:
            self.name = self.source_path.name

    @property
    def is_available(self) -> bool:
        return zarr_backend_available()

    def load(self) -> xr.Dataset:
        if not self.is_available:
            warn_once(
                f"Zarr input backend unavailable for '{self.reference}'. Falling back to empty dataset."
            )
            return _fallback_dataset(self.source_name)
        try:
            opened = xr.open_zarr(self.source_path)
            dataset = opened.load()
            close = getattr(opened, "close", None)
            if callable(close):
                close()
        except Exception as exc:
            warn_once(
                f"Failed to read Zarr input '{self.reference}': {exc}. Falling back to empty dataset."
            )
            dataset = _fallback_dataset(self.source_name)
        else:
            if isinstance(dataset, xr.DataArray):
                dataset = dataset.to_dataset(name=dataset.name or "value")
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
            warn_once(f"Zarr output backend unavailable for '{self.reference}'. Skipping write.")
            return False
        return _write_zarr(dataset, self.source_path, self.reference)


class ZarrOutputAdapter(OutputAdapter):
    format_name = "zarr"

    @property
    def is_available(self) -> bool:
        return zarr_backend_available()

    def target_path(self, data_input: DataInput) -> Path:
        if data_input.source_path is None:
            raise ValueError("Zarr output requires a path-based input")
        return data_input.source_path.with_suffix(".zarr")

    def save(self, dataset: xr.Dataset, data_input: DataInput, dry_run: bool = True) -> bool:
        if dry_run:
            return False
        if not self.is_available:
            warn_once(
                f"Zarr output backend unavailable for '{data_input.reference}'. Skipping write."
            )
            return False
        target = self.target_path(data_input)
        return _write_zarr(dataset, target, str(target))


# ---------------------------------------------------------------------------
# Backend plugin interface
# ---------------------------------------------------------------------------

BACKEND_NAME = "zarr"


def is_available() -> bool:
    return zarr_backend_available()


def can_open(source: Any) -> bool:
    if isinstance(source, (str, PathLike, Path)):
        path = Path(source)
        return path.suffix.lower() == ".zarr"
    return False


def create_input(source: Any) -> ZarrInput:
    path = Path(source)
    return ZarrInput(source_path=path, name=path.name)


def create_output_adapter() -> ZarrOutputAdapter:
    return ZarrOutputAdapter()