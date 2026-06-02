from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

# Importing woodpecker.fixes registers built-in fixes before API selection runs.
import woodpecker.fixes  # noqa: F401
from woodpecker.commands import execute_check, execute_check_recipe, execute_fix, execute_fix_recipe
from woodpecker.recipes.models import Recipe
from woodpecker.results import CheckResult, FixResult
from woodpecker.stores.helpers import create_recipe_store


@dataclass(frozen=True)
class RecipeSelector:
    """Recipe source selector for the public recipe API."""

    recipe: str | Path | None
    recipe_id: str | None = None
    store_type: str = "json"


RecipeSource = str | Path | None | RecipeSelector | Recipe


def auto(recipe_id: str | None = None) -> RecipeSelector:
    """Select generated one-step recipes from registered fixes."""
    return RecipeSelector(recipe=None, recipe_id=recipe_id, store_type="auto")


def catalog(recipe_id: str | None = None, recipe: str | Path | None = None) -> RecipeSelector:
    """Select recipes from discovered package, user, system, and optional explicit locations."""
    return RecipeSelector(recipe=recipe, recipe_id=recipe_id, store_type="catalog")


discovered = catalog


def get(recipe_id: str, recipe: str | Path | None = None) -> Recipe:
    """Load a discovered recipe by id or alias."""
    return create_recipe_store("catalog", Path(recipe) if recipe is not None else None).get_recipe(
        recipe_id
    )


def list_recipes(recipe: str | Path | None = None) -> list[Recipe]:
    """List discovered recipes."""
    return create_recipe_store("catalog", Path(recipe) if recipe is not None else None).list_recipes()


def _normalize_fixes(fixes: str | Sequence[str] | None) -> tuple[str, ...]:
    if fixes is None:
        return ()
    if isinstance(fixes, str):
        return (fixes,)
    return tuple(str(item) for item in fixes)


def _resolve_recipe_source(
    recipe: RecipeSource,
    *,
    recipe_id: str | None,
    store_type: str,
) -> tuple[str | Path | None, str | None, str]:
    if isinstance(recipe, RecipeSelector):
        return recipe.recipe, recipe_id or recipe.recipe_id, recipe.store_type
    return recipe, recipe_id, store_type


def _resolve_recipe_selection(
    recipe: Recipe,
    fixes: str | Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, dict[str, Any]]]:
    source_identifiers, source_fix_options = recipe.step_identifiers_and_options()
    resolved_identifiers = _normalize_fixes(fixes) or source_identifiers
    return resolved_identifiers, resolved_identifiers, dict(source_fix_options)


def check(
    inputs: Any,
    recipe: RecipeSource,
    *,
    recipe_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    strict_io: bool = False,
) -> CheckResult:
    """Check inputs using fixes selected from a recipe."""
    if isinstance(recipe, Recipe):
        resolved_identifiers, ordered_identifiers, fix_options = _resolve_recipe_selection(
            recipe,
            fixes,
        )
        return CheckResult(
            findings=tuple(
                execute_check(
                    inputs,
                    dataset=dataset,
                    categories=categories,
                    identifiers=resolved_identifiers,
                    fix_options=fix_options,
                    ordered_identifiers=ordered_identifiers,
                    strict_io=strict_io,
                )
            )
        )

    recipe_location, resolved_recipe_id, resolved_store_type = _resolve_recipe_source(
        recipe,
        recipe_id=recipe_id,
        store_type=store_type,
    )
    return CheckResult(
        findings=tuple(
            execute_check_recipe(
                recipe_location,
                inputs=inputs,
                dataset=dataset,
                categories=categories,
                identifiers=_normalize_fixes(fixes),
                recipe_id=resolved_recipe_id,
                store_type=resolved_store_type,
                strict_io=strict_io,
            )
        )
    )


def fix(
    inputs: Any,
    recipe: RecipeSource,
    *,
    recipe_id: str | None = None,
    store_type: str = "json",
    dataset: str | None = None,
    categories: Sequence[str] = (),
    fixes: str | Sequence[str] | None = None,
    dry_run: bool = True,
    output_format: str = "auto",
    strict_io: bool = False,
) -> FixResult:
    """Apply fixes selected from a recipe."""
    if isinstance(recipe, Recipe):
        resolved_identifiers, ordered_identifiers, fix_options = _resolve_recipe_selection(
            recipe,
            fixes,
        )
        return FixResult(
            stats=execute_fix(
                inputs,
                dataset=dataset,
                categories=categories,
                identifiers=resolved_identifiers,
                dry_run=dry_run,
                output_format=output_format,
                fix_options=fix_options,
                ordered_identifiers=ordered_identifiers,
                strict_io=strict_io,
            )
        )

    recipe_location, resolved_recipe_id, resolved_store_type = _resolve_recipe_source(
        recipe,
        recipe_id=recipe_id,
        store_type=store_type,
    )
    return FixResult(
        stats=execute_fix_recipe(
            recipe_location,
            inputs=inputs,
            dataset=dataset,
            categories=categories,
            identifiers=_normalize_fixes(fixes),
            dry_run=dry_run,
            output_format=output_format,
            recipe_id=resolved_recipe_id,
            store_type=resolved_store_type,
            strict_io=strict_io,
        )
    )
