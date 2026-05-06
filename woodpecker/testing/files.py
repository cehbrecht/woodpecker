"""Small file helpers used by tests and examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: Any) -> Path:
    """Write JSON payload to ``path`` and return the resolved path object."""
    target = Path(path)
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def write_plan_document(path: str | Path, plans: list[dict[str, Any]]) -> Path:
    """Write a fix-plan document with a top-level ``plans`` key."""
    return write_json(path, {"plans": plans})