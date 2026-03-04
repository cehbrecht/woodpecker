from __future__ import annotations

from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, Iterable, List, Sequence


def _is_xarray_object(value: Any) -> bool:
    module = getattr(value.__class__, "__module__", "")
    return module.startswith("xarray.")


def _is_pathlike(value: Any) -> bool:
    return isinstance(value, (str, PathLike, Path))


@dataclass
class DataInput:
    payload: Any = None
    source_path: Path | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def source_name(self) -> str:
        if self.source_path is not None:
            return self.source_path.name
        if self.name:
            return self.name

        attrs = getattr(self.payload, "attrs", None)
        if isinstance(attrs, dict):
            for key in ("source_name", "name", "id"):
                value = attrs.get(key)
                if isinstance(value, str) and value:
                    return value

        payload_name = getattr(self.payload, "name", None)
        if isinstance(payload_name, str) and payload_name:
            return payload_name

        return "<in-memory>"

    @property
    def reference(self) -> str:
        if self.source_path is not None:
            return str(self.source_path)
        return self.source_name


def collect_netcdf_files(paths: Sequence[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".nc":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.nc")))
    return files


def _as_data_input(value: Any) -> list[DataInput]:
    if isinstance(value, DataInput):
        return [value]

    if _is_pathlike(value):
        path = Path(value)
        if path.is_dir():
            return [
                DataInput(source_path=file_path, name=file_path.name)
                for file_path in collect_netcdf_files([path])
            ]
        if path.is_file() and path.suffix.lower() == ".nc":
            return [DataInput(source_path=path, name=path.name)]
        raise ValueError(f"Unsupported path input: {path}")

    if _is_xarray_object(value):
        return [DataInput(payload=value)]

    raise TypeError(f"Unsupported input type: {type(value)!r}")


def normalize_inputs(inputs: Any) -> List[DataInput]:
    if _is_pathlike(inputs) or _is_xarray_object(inputs) or isinstance(inputs, DataInput):
        return _as_data_input(inputs)

    if isinstance(inputs, Iterable):
        normalized: List[DataInput] = []
        for item in inputs:
            normalized.extend(_as_data_input(item))
        return normalized

    return _as_data_input(inputs)
