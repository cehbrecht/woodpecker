from __future__ import annotations

from typing import Any


def project_id_from_dataset_id(dataset_id: str) -> str:
    if not dataset_id:
        return ""
    return dataset_id.split(".", 1)[0]


def first_str_attr(attrs: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalized_token(value: str | None) -> str:
    return str(value or "").strip().lower()
