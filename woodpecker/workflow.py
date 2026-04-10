from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class WorkflowSpec(BaseModel):
    """Declarative workflow definition for selecting and running fixes."""

    version: int = 1
    name: str = ""
    inputs: List[str] = Field(default_factory=list)
    dataset: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    codes: List[str] = Field(default_factory=list)
    fixes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    output_format: Optional[str] = Field(default=None, pattern=r"^(auto|netcdf|zarr)$")
    requires: List[str] = Field(default_factory=list)

    @field_validator("inputs", "categories", "codes", "requires", mode="before")
    @classmethod
    def _ensure_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @field_validator("fixes", mode="before")
    @classmethod
    def _normalize_fixes(cls, value: Any) -> dict[str, dict[str, Any]]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("fixes must be a mapping from fix code to options")

        normalized: dict[str, dict[str, Any]] = {}
        for key, options in value.items():
            code = str(key).strip().upper()
            if not code:
                raise ValueError("fixes contains an empty fix code key")
            if options is None:
                normalized[code] = {}
                continue
            if not isinstance(options, dict):
                raise ValueError(f"fixes['{code}'] must be an object/mapping")
            normalized[code] = dict(options)
        return normalized


SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}


def _load_payload(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if suffix == ".json":
        payload = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise ValueError(
                "YAML workflow files require PyYAML. Install with: pip install pyyaml "
                "or use a .json workflow file."
            ) from exc
        payload = yaml.safe_load(text)
    else:
        raise ValueError(
            f"Unsupported workflow extension '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if not isinstance(payload, dict):
        raise ValueError("Workflow file must define a JSON/YAML object at top level")
    return payload


def load_workflow(path: Path) -> WorkflowSpec:
    if not path.exists():
        raise ValueError(f"Workflow file not found: {path}")

    payload = _load_payload(path)
    try:
        return WorkflowSpec.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid workflow file '{path}': {exc}") from exc
