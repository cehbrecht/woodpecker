from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from .models import FixPlan, parse_fix_ref
from .spec import FixPlanSpec

try:
    import yaml
except Exception:  # pragma: no cover - optional import guard
    yaml = None


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
        return FixPlan(fixes=[parse_fix_ref(item) for item in payload])
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
