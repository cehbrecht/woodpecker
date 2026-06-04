# User-Friendliness Memory

This page is a working memory for future usability work. It should not repeat
things that are already implemented. The next topic to clarify is recipe
vocabulary.

## Recipe Vocabulary

The clearest user model is:

- **recipe**: a reusable workflow definition,
- **get** or **load**: retrieve a recipe,
- **preview**: inspect what the recipe would do,
- **apply** or **run**: execute the recipe,
- **fix**: a lower-level operation used inside a recipe step.

This keeps nouns and verbs separate. A user should be able to think:

```python
recipe = woodpecker.recipe.get("xmip.cmip6_preprocessing")
preview = woodpecker.recipe.preview(dataset, recipe)
result = woodpecker.recipe.apply(dataset, recipe)
```

The CLI could follow the same shape:

```bash
woodpecker recipe list
woodpecker recipe show xmip.cmip6_preprocessing
woodpecker recipe preview file.nc xmip.cmip6_preprocessing
woodpecker recipe apply file.nc xmip.cmip6_preprocessing
```

`apply` is probably clearer than `run` when data may be changed. `run` can still
be useful as a generic term, but user-facing mutation should prefer `apply`.

## Optional Fix Dependencies

Woodpecker already has fix priorities. Dependencies could be added later as a
stronger, optional ordering contract, but this should stay small and explicit.

A possible first shape:

```python
class NormalizeBounds(FixFunction):
    dependencies = ["woodpecker.rename_variables"]
```

The dependency list would mean: if this fix is selected, the listed fixes must
run first. A resolver could then:

1. take selected fix ids,
2. optionally add required dependencies,
3. topologically sort fixes,
4. use priority only as a tie-breaker,
5. fail clearly on cycles or missing dependencies.

This should not become a full workflow engine. No conditional dependencies,
conflicts, or dataset-specific graph rules at first. Recipes should remain the
main user-facing workflow concept; a fix resolver would mostly support recipes
and direct fix selection.

## Questions For The Next PR

- Should the public Python API add `woodpecker.recipe.preview(...)` as a clearer
  alias or replacement for dry-run `recipe.fix(...)`?
- Should `woodpecker.recipe.apply(...)` become the preferred mutation verb?
- Should CLI recipe commands become a grouped command surface, or should the
  existing `check` and `fix` commands keep recipe options?
- Where does `check` fit: is it a separate validation phase, or part of
  `recipe preview`?
- How much old `fix` wording should remain visible to users versus only in
  contributor/plugin documentation?
- Should fix dependencies be declared only as required predecessors, or do we
  also need softer ordering hints such as `runs_after`?

## Documentation Work

Future docs should explain that Woodpecker recipes are repair recipes for
checking, previewing, and applying dataset fixes. This should be explicit enough
to avoid confusion with ESMValTool analysis recipes while still using the shared
mental model of a configured workflow.

Good examples should show the lifecycle:

1. find or load a recipe,
2. preview it on a dataset,
3. apply it when the preview looks right,
4. inspect the result.
