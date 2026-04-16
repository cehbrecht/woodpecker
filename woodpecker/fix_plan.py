from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError, field_validator

try:
    import yaml
except Exception:  # pragma: no cover - optional import guard
    yaml = None


@dataclass
class FixRef:
    """Reference to one fix and its optional options payload."""

    id: str
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = str(self.id).strip().upper()
        if not self.id:
            raise ValueError("FixRef.id must be a non-empty string")
        if not isinstance(self.options, dict):
            raise ValueError("FixRef.options must be a mapping/object")


@dataclass
class FixPlan:
    """A lightweight data structure describing fixes to execute."""

    fixes: list[FixRef] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> FixPlan:
        items = payload.get("fixes", [])
        if not isinstance(items, list):
            raise ValueError("FixPlan 'fixes' must be a list")
        return cls(fixes=[_parse_fix_ref(item) for item in items])


def _parse_fix_ref(item: Any) -> FixRef:
    if isinstance(item, str):
        return FixRef(id=item)
    if not isinstance(item, Mapping):
        raise ValueError("Each fix entry must be a string or object")
    fix_id = item.get("id", item.get("code", ""))
    return FixRef(id=str(fix_id), options=dict(item.get("options", {}) or {}))


def _resolve_fix(registry: Any, fix_id: str) -> Any:
    key = str(fix_id).strip().upper()
    source: Any | None = None
    if isinstance(registry, Mapping):
        source = registry.get(key)
    elif hasattr(registry, "_registry"):
        source = getattr(registry, "_registry", {}).get(key)
    elif hasattr(registry, "get"):
        source = registry.get(key)

    if source is None:
        raise KeyError(f"Unknown fix id: {key}")

    if isinstance(source, type):
        return source()
    if callable(source) and not hasattr(source, "check"):
        return source()
    return source


def apply_plan(ds: Any, plan: FixPlan, registry: Any) -> Any:
    """Resolve plan fix ids from a registry and execute check then fix/apply."""

    for ref in plan.fixes:
        fix = _resolve_fix(registry, ref.id)

        if hasattr(fix, "configure"):
            fix = fix.configure(ref.options)

        if not hasattr(fix, "check"):
            raise TypeError(f"Fix '{ref.id}' does not implement check()")
        _invoke_with_optional_options(fix.check, ds, ref.options)

        if hasattr(fix, "fix"):
            _invoke_with_optional_options(fix.fix, ds, ref.options)
        elif hasattr(fix, "apply"):
            fix.apply(ds, dry_run=False)
        else:
            raise TypeError(f"Fix '{ref.id}' does not implement fix() or apply()")

    return ds


def _invoke_with_optional_options(method: Any, ds: Any, options: Mapping[str, Any]) -> Any:
    """Call fix method and pass options only when the signature supports it."""

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        # If signature introspection is unavailable, preserve prior behavior.
        return method(ds, options=options)

    parameters = signature.parameters.values()
    supports_options = any(
        param.kind is inspect.Parameter.VAR_KEYWORD or param.name == "options"
        for param in parameters
    )
    if supports_options:
        return method(ds, options=options)
    return method(ds)


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


class PlanStep(BaseModel):
    code: str
    comment: Optional[str] = None
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

    @field_validator("comment", mode="before")
    @classmethod
    def _normalize_comment(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class DatasetFixPlan(BaseModel):
    dataset: Optional[str] = None
    comment: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    codes: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(default_factory=list)
    fixes: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("comment", mode="before")
    @classmethod
    def _normalize_comment(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

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
class FixPlanResolution:
    dataset: Optional[str]
    categories: list[str]
    plan: FixPlan
    ordered_ids: list[str]
    output_format: Optional[str]
    requires: list[str]

    @property
    def codes(self) -> list[str]:
        return [item.id for item in self.plan.fixes]

    @property
    def fixes(self) -> dict[str, dict[str, Any]]:
        return {item.id: dict(item.options) for item in self.plan.fixes}


class FixPlanSpec(BaseModel):
    """Declarative fix plan definition for selecting and running fixes."""

    version: int = 1
    name: str = ""
    comment: Optional[str] = None
    inputs: list[str] = Field(default_factory=list)
    dataset: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    codes: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(default_factory=list)
    datasets: dict[str, DatasetFixPlan] = Field(default_factory=dict)
    fixes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    output_format: Optional[str] = Field(default=None, pattern=r"^(auto|netcdf|zarr)$")
    requires: list[str] = Field(default_factory=list)

    @field_validator("inputs", "categories", "requires", mode="before")
    @classmethod
    def _ensure_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @field_validator("comment", mode="before")
    @classmethod
    def _normalize_comment(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

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
            raise ValueError("datasets must be a mapping from selector to plan block")

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
            raise ValueError(f"datasets['{key}'] must be a list or mapping")
        return normalized

    def _match_dataset_block(self, references: Sequence[str]) -> DatasetFixPlan | None:
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

    def resolve(self, references: Sequence[str]) -> FixPlanResolution:
        block = self._match_dataset_block(references)

        block_dataset = block.dataset if block else None
        block_categories = list(block.categories) if block else []
        block_codes = list(block.codes) if block else []
        block_steps = list(block.steps) if block else []
        block_fixes = dict(block.fixes) if block else {}

        steps = block_steps or list(self.steps)
        ordered_ids = [step.code for step in steps]

        step_fixes: dict[str, dict[str, Any]] = {}
        for step in steps:
            if step.options:
                step_fixes.setdefault(step.code, {})
                step_fixes[step.code].update(step.options)

        if ordered_ids:
            codes = block_codes or ordered_ids
        else:
            codes = block_codes or list(self.codes)

        options_map = _merge_fix_options(self.fixes, block_fixes, step_fixes)
        plan = FixPlan(fixes=[FixRef(id=code, options=options_map.get(code, {})) for code in codes])

        return FixPlanResolution(
            dataset=block_dataset or self.dataset,
            categories=block_categories or list(self.categories),
            plan=plan,
            ordered_ids=ordered_ids,
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
        if yaml is None:
            raise ValueError(
                "YAML fix plan files require PyYAML. Install with: pip install pyyaml or use .json"
            )
        payload = yaml.safe_load(text)
    else:
        raise ValueError(
            f"Unsupported fix plan extension '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if not isinstance(payload, dict):
        raise ValueError("Fix plan file must define a JSON/YAML object at top level")
    return payload


def load_fix_plan(path: str | Path) -> FixPlan:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise ValueError("YAML support requires PyYAML")
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Unsupported fix plan file extension; use .json, .yaml, or .yml")

    if payload is None:
        payload = {"fixes": []}
    if isinstance(payload, list):
        return FixPlan(fixes=[_parse_fix_ref(item) for item in payload])
    if not isinstance(payload, Mapping):
        raise ValueError("Fix plan file must contain an object or list")

    return FixPlan.from_mapping(payload)


def load_fix_plan_spec(path: str | Path) -> FixPlanSpec:
    file_path = Path(path)
    if not file_path.exists():
        raise ValueError(f"Fix plan file not found: {file_path}")

    payload = _load_payload(file_path)
    try:
        return FixPlanSpec.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid fix plan file '{file_path}': {exc}") from exc
