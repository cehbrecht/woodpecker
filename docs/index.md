# Woodpecker

Woodpecker is a lightweight, code-driven fix catalog for climate datasets.

- **Fix IDs** are stable canonical identifiers (e.g. `cmip6_decadal.time_metadata`) that external systems (like an ESGF errata UI) can reference.
- The catalog can be exported as **Markdown** (`FIXES.md`) and **JSON** (`FIXES.json`), and rendered as a small interactive web page (`fixes.html`).
- Catalog entries include a **Source** value: `core` for built-in fixes, and `plugin:<package>` for plugin-discovered fixes.
