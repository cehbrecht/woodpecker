from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

from .models import FixPlan


def plan_matches_dataset(plan: FixPlan, dataset: Any, path: str | None = None) -> bool:
    matcher = plan.match
    if matcher is None:
        return True

    attrs_ok = True
    if matcher.attrs:
        dataset_attrs = getattr(dataset, "attrs", None)
        if not isinstance(dataset_attrs, dict):
            dataset_attrs = dict(dataset_attrs or {})
        attrs_ok = all(dataset_attrs.get(key) == value for key, value in matcher.attrs.items())

    path_ok = True
    if matcher.path_patterns:
        if path is None:
            path_ok = False
        else:
            path_text = str(path)
            path_ok = any(fnmatch(path_text, pattern) for pattern in matcher.path_patterns)

    return attrs_ok and path_ok
