from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence, TypedDict

from woodpecker.io import DataInput, normalize_inputs
from woodpecker.runner import run_check, run_fix
from woodpecker.selection import select_fixes

if TYPE_CHECKING:
    from woodpecker.recipes.resolver import RunContext


class RunFixKwargs(TypedDict, total=False):
    """Keyword arguments accepted by run_fix for command-level orchestration."""

    dry_run: bool
    output_format: str
    force_apply: bool
    embed_provenance_metadata: bool
    provenance_run_id: str
    strict_io: bool


def _resolve_recipe_api_selection(
    *,
    recipe_path: str | Path | None,
    inputs: Any | None,
    identifiers: Sequence[str],
    recipe_id: str | None,
    store_type: str,
) -> tuple[list[DataInput], tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    from woodpecker.recipes.resolver import resolve_recipe_source, resolve_selection_inputs

    resolved_inputs = inputs if inputs is not None else [Path.cwd()]
    normalized = normalize_inputs(resolved_inputs)
    _, _, source_identifiers, source_fix_options = resolve_recipe_source(
        inputs=normalized,
        store_type=store_type,
        recipe_location=Path(recipe_path) if recipe_path is not None else None,
        recipe_id=recipe_id,
    )
    resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        resolve_selection_inputs(
            cli_identifiers=identifiers,
            source_identifiers=source_identifiers,
            source_fix_options=source_fix_options,
        )
    )
    return normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options


def execute_check(
    inputs: Any,
    *,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
    strict_io: bool = False,
) -> list[dict[str, str]]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_check(normalized, fixes, strict_io=strict_io)


def execute_fix(
    inputs: Any,
    *,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    dry_run: bool = True,
    output_format: str = "auto",
    fix_options: dict[str, dict[str, Any]] | None = None,
    ordered_identifiers: Sequence[str] = (),
    strict_io: bool = False,
) -> dict[str, int]:
    normalized = normalize_inputs(inputs)
    fixes = select_fixes(
        dataset=dataset,
        categories=categories,
        identifiers=identifiers,
        strict_identifiers=True,
        fix_options=fix_options,
        ordered_identifiers=ordered_identifiers,
    )
    return run_fix(
        normalized,
        fixes,
        dry_run=dry_run,
        output_format=output_format,
        strict_io=strict_io,
    )


def execute_check_recipe(
    recipe_path: str | Path | None,
    *,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    recipe_id: str | None = None,
    store_type: str = "json",
    strict_io: bool = False,
) -> list[dict[str, str]]:
    normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        _resolve_recipe_api_selection(
            recipe_path=recipe_path,
            inputs=inputs,
            identifiers=identifiers,
            recipe_id=recipe_id,
            store_type=store_type,
        )
    )

    return execute_check(
        normalized,
        dataset=dataset,
        categories=categories,
        identifiers=resolved_identifiers,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
        strict_io=strict_io,
    )


def execute_fix_recipe(
    recipe_path: str | Path | None,
    *,
    inputs: Any | None = None,
    dataset: str | None = None,
    categories: Sequence[str] = (),
    identifiers: Sequence[str] = (),
    dry_run: bool = True,
    output_format: str = "auto",
    recipe_id: str | None = None,
    store_type: str = "json",
    strict_io: bool = False,
) -> dict[str, int]:
    normalized, resolved_identifiers, resolved_ordered_identifiers, resolved_fix_options = (
        _resolve_recipe_api_selection(
            recipe_path=recipe_path,
            inputs=inputs,
            identifiers=identifiers,
            recipe_id=recipe_id,
            store_type=store_type,
        )
    )

    return execute_fix(
        normalized,
        dataset=dataset,
        categories=categories,
        identifiers=resolved_identifiers,
        dry_run=dry_run,
        output_format=output_format,
        fix_options=resolved_fix_options,
        ordered_identifiers=resolved_ordered_identifiers,
        strict_io=strict_io,
    )


def execute_check_context(
    context: "RunContext",
    *,
    strict_io: bool = False,
) -> list[dict[str, str]]:
    """Run check execution from a pre-resolved run context."""

    return run_check(context.inputs, context.fixes, strict_io=strict_io)


def build_run_fix_kwargs(
    *,
    output_format: str,
    dry_run: bool,
    force_apply: bool,
    embed_provenance_metadata: bool,
    provenance_run_id: str | None,
    strict_io: bool,
) -> RunFixKwargs:
    """Build run_fix kwargs from command-level execution flags."""

    run_fix_kwargs: RunFixKwargs = {
        "dry_run": dry_run,
        "output_format": output_format,
        "strict_io": strict_io,
    }
    if force_apply:
        run_fix_kwargs["force_apply"] = True
    if embed_provenance_metadata and not dry_run:
        run_fix_kwargs["embed_provenance_metadata"] = True
        run_fix_kwargs["provenance_run_id"] = provenance_run_id or ""
    return run_fix_kwargs


def execute_fix_context(
    context: "RunContext",
    *,
    dry_run: bool,
    force_apply: bool,
    embed_provenance_metadata: bool,
    provenance_run_id: str | None,
    strict_io: bool = False,
) -> dict[str, int]:
    """Run fix execution from a pre-resolved run context."""

    if force_apply and not context.resolved_identifiers:
        raise ValueError(
            "--force-apply requires explicit fix selection via --select or recipe identifiers."
        )
    run_fix_kwargs = build_run_fix_kwargs(
        output_format=context.resolved_output_format,
        dry_run=dry_run,
        force_apply=force_apply,
        embed_provenance_metadata=embed_provenance_metadata,
        provenance_run_id=provenance_run_id,
        strict_io=strict_io,
    )
    return run_fix(context.inputs, context.fixes, **run_fix_kwargs)


def execute_load_recipes(
    store_type: str,
    recipe_location: Path,
    from_recipe: Path | None,
    from_store: str,
    recipe_id: str | None = None,
) -> dict:
    """Load recipes into a target store from a source store location."""
    from woodpecker.recipes.resolver import resolve_load_source_recipes
    from woodpecker.stores.helpers import create_recipe_store

    target_store = create_recipe_store(store_type, recipe_location)
    recipes = resolve_load_source_recipes(
        from_recipe=from_recipe,
        from_store_type=from_store,
        recipe_id=recipe_id,
    )
    for recipe in recipes:
        target_store.save_recipe(recipe)
    recipe_ids = [recipe.id or "<unnamed>" for recipe in recipes]
    return {
        "loaded": len(recipes),
        "target_store": store_type,
        "target_path": str(recipe_location),
        "recipe_ids": recipe_ids,
    }
