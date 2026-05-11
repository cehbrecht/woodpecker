# Woodpecker

Woodpecker is a lightweight, code-driven fix catalog for climate datasets.

- **Fix IDs** are stable `prefix.suffix` identifiers (e.g. `cmip6_decadal.time_metadata`) that external systems (like an ESGF errata UI) can reference.
- The catalog can be exported as **Markdown** (`FIXES.md`) and **JSON** (`FIXES.json`), and rendered as a small interactive web page (`fixes.html`).
- **Fix plans** are documented in `FIX_PLANS.md` to help users choose a recipe for matching datasets.
- **Auto plans** expose registered fixes as single-step plans when no curated plan document exists yet.
- **FixPlanCatalog** can combine multiple plan sources, such as local plan files and auto-generated plans.
- Catalog entries include a **Source** value: `core` for built-in fixes, and `plugin:<package>` for plugin-discovered fixes.
- The **Design Notes** page defines the vocabulary for fixes, fix plans, documents, stores, and catalogs.
- Executed notebook examples are available under **Examples**.
