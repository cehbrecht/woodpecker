from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, List, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError, field_validator


def _normalize_code_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    else:
        items = list(value)
    return [str(item).strip().upper() for item in items if str(item).strip()]


def _merge_fix_options(*maps: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for mapping in maps:
        for code, options in (mapping or {}).items():
            key = str(code).strip().upper()
            if not key:
                continue
            merged.setdefault(key, {})
            merged[key].update(dict(options or {}))
    return merged


class WorkflowStep(BaseModel):
    code: str
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code", mode="before")
    @classmethod
    def _normalize_code(cls, value: Any) -> str:
        code = str(value).strip().upper()
        if not code:
            raise ValueError("step code must be a non-empty string")
        return code

    @field_validator("options", mode="before")
    @classmethod
    def _normalize_options(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("step options must be an object/mapping")
        return dict(value)


class DatasetWorkflow(BaseModel):
    dataset: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    codes: List[str] = Field(default_factory=list)
    steps: List[WorkflowStep] = Field(default_factory=list)
    fixes: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("categories", mode="before")
    @classmethod
    def _ensure_categories(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @field_validator("codes", mode="before")
    @classmethod
    def _ensure_codes(cls, value: Any) -> list[str]:
        return _normalize_code_list(value)

    @field_validator("fixes", mode="before")
    @classmethod
    def _normalize_fixes(cls, value: Any) -> dict[str, dict[str, Any]]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("fixes must be a mapping from fix code to options")
        out: dict[str, dict[str, Any]] = {}
        for key, options in value.items():
            code = str(key).strip().upper()
            if not code:
                continue
            if options is None:
                out[code] = {}
                continue
            if not isinstance(options, dict):
                raise ValueError(f"fixes['{code}'] must be an object/mapping")
            out[code] = dict(options)
        return out


@dataclass(frozen=True)
class WorkflowResolution:
    dataset: Optional[str]
    categories: List[str]
    codes: List[str]
    ordered_codes: List[str]
    fixes: dict[str, dict[str, Any]]
    output_format: Optional[str]
    requires: List[str]


class WorkflowSpec(BaseModel):
    """Declarative workflow definition for selecting and running fixes."""

    version: int = 1
    name: str = ""
    inputs: List[str] = Field(default_factory=list)
    dataset: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    codes: List[str] = Field(default_factory=list)
    steps: List[WorkflowStep] = Field(default_factory=list)
    datasets: dict[str, DatasetWorkflow] = Field(default_factory=dict)
    fixes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    output_format: Optional[str] = Field(default=None, pattern=r"^(auto|netcdf|zarr)$")
    requires: List[str] = Field(default_factory=list)

    @field_validator("inputs", "categories", "requires", mode="before")
    @classmethod
    def _ensure_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @field_validator("codes", mode="before")
    @classmethod
    def _ensure_codes(cls, value: Any) -> list[str]:
        return _normalize_code_list(value)

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

    @field_validator("datasets", mode="before")
    @classmethod
    def _normalize_datasets(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("datasets must be a mapping from selector to workflow block")

        normalized: dict[str, Any] = {}
        for selector, block in value.items():
            key = str(selector).strip()
            if not key:
                raise ValueError("datasets contains an empty selector key")
            if isinstance(block, list):
                normalized[key] = {"steps": block}
                continue
            if isinstance(block, dict):
                normalized[key] = block
                continue
            raise ValueError(
                f"datasets['{key}'] must be either a list of step objects or a mapping"
            )
        return normalized

    def _match_dataset_block(self, references: Sequence[str]) -> DatasetWorkflow | None:
        if not self.datasets:
            return None
        for selector, block in self.datasets.items():
            for reference in references:
                ref = str(reference)
                name = Path(ref).name
                if selector == ref or selector == name:
                    return block
                if fnmatch(ref, selector) or fnmatch(name, selector):
                    return block
        return None

    def resolve(self, references: Sequence[str]) -> WorkflowResolution:
        block = self._match_dataset_block(references)

        block_dataset = block.dataset if block else None
        block_categories = list(block.categories) if block else []
        block_codes = list(block.codes) if block else []
        block_steps = list(block.steps) if block else []
        block_fixes = dict(block.fixes) if block else {}

        steps = block_steps or list(self.steps)
        ordered_codes = [step.code for step in steps]

        step_fixes: dict[str, dict[str, Any]] = {}
        for step in steps:
            if step.options:
                step_fixes.setdefault(step.code, {})
                step_fixes[step.code].update(step.options)

        if ordered_codes:
            codes = block_codes or ordered_codes
        else:
            codes = block_codes or list(self.codes)

        fixes = _merge_fix_options(self.fixes, block_fixes, step_fixes)

        return WorkflowResolution(
            dataset=block_dataset or self.dataset,
            categories=block_categories or list(self.categories),
            codes=codes,
            ordered_codes=ordered_codes,
            fixes=fixes,
            output_format=self.output_format,
            requires=list(self.requires),
        )


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
