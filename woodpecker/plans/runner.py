from __future__ import annotations

import inspect
from typing import Any, Mapping

from .models import FixPlan


def resolve_fix(registry: Any, fix_id: str) -> Any:
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


def invoke_with_optional_options(method: Any, ds: Any, options: Mapping[str, Any]) -> Any:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(ds, options=options)

    parameters = signature.parameters.values()
    supports_options = any(
        param.kind is inspect.Parameter.VAR_KEYWORD or param.name == "options"
        for param in parameters
    )
    if supports_options:
        return method(ds, options=options)
    return method(ds)


def apply_fix_plan(ds: Any, plan: FixPlan, registry: Any) -> Any:
    """Resolve plan fix ids and apply fixes in order.

    For each fix: call check(), then call fix()/apply() when check result indicates apply.
    """

    for ref in plan.fixes:
        fix = resolve_fix(registry, ref.id)

        if hasattr(fix, "configure"):
            fix = fix.configure(ref.options)

        if not hasattr(fix, "check"):
            raise TypeError(f"Fix '{ref.id}' does not implement check()")
        should_apply = invoke_with_optional_options(fix.check, ds, ref.options)
        if not isinstance(should_apply, bool):
            # Backward-compatible behavior for legacy fixes with non-bool check output.
            should_apply = True

        if not should_apply:
            continue

        if hasattr(fix, "fix"):
            invoke_with_optional_options(fix.fix, ds, ref.options)
        elif hasattr(fix, "apply"):
            fix.apply(ds, dry_run=False)
        else:
            raise TypeError(f"Fix '{ref.id}' does not implement fix() or apply()")

    return ds
