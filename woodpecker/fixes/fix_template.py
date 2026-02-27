"""Pydantic-ready template (optional).

This file is intentionally NOT imported by default to keep core dependencies light.
If/when you decide to adopt Pydantic, you can use this as a starting point.

Requires:
    pip install pydantic
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

try:
    from pydantic import BaseModel, Field, field_validator
except Exception as e:  # pragma: no cover
    raise ImportError(
        "Pydantic is not installed. Install with: pip install pydantic"
    ) from e

from .registry import FixRegistry


class FixModel(BaseModel):
    code: str = Field(..., pattern=r"^[A-Z0-9]{4,12}$", description="Unique fix code")
    name: str
    description: str = ""
    categories: List[str] = []
    priority: int = 10
    dataset: Optional[str] = None

    @field_validator("categories", mode="before")
    @classmethod
    def ensure_categories_list(cls, v):
        return v or []

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() == ".nc"

    def check(self, path: Path) -> List[str]:
        return []

    def apply(self, path: Path, dry_run: bool = True) -> bool:
        return False


@FixRegistry.register
class EX01(FixModel):
    code: str = "EX01"
    name: str = "Example fix"
    description: str = "Example fix defined via a Pydantic model."
    categories: List[str] = ["metadata"]
    priority: int = 999
    dataset: str = "Example"
