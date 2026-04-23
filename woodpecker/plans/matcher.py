from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, Mapping

from .models import FixPlan


def _match_attrs(dataset: Any, expected_attrs: Mapping[str, Any]) -> bool:
    """Return True when all expected dataset attrs match exactly.

    Matching is AND-based across declared attributes.
    """

    if not expected_attrs:
        return True

    dataset_attrs = getattr(dataset, "attrs", None)
    if isinstance(dataset_attrs, Mapping):
        attrs = dict(dataset_attrs)
    else:
        attrs = dict(dataset_attrs or {})

    return all(attrs.get(key) == value for key, value in expected_attrs.items())


def _match_path_patterns(path: str | None, patterns: list[str]) -> bool:
    """Return True when any pattern matches the provided path string.

    Path patterns are matched against the provided `path` text (not dataset attrs).
    """

    if not patterns:
        return True
    if path is None:
        return False

    path_text = str(path)
    return any(fnmatch(path_text, pattern) for pattern in patterns)


def plan_matches_dataset(plan: FixPlan, dataset: Any, path: str | None = None) -> bool:
    """Return True when dataset satisfies all declared plan match constraints.

    Semantics are AND-based:
    - attribute constraints must all pass
    - path pattern constraints must pass when declared
    """

    matcher = plan.match
    if matcher is None:
        return True

    attrs_ok = _match_attrs(dataset, matcher.attrs)
    path_ok = _match_path_patterns(path, matcher.path_patterns)

    return attrs_ok and path_ok
