from __future__ import annotations

import json
from pathlib import Path

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry, GroupFix


def generate_catalog(md_path: str = "docs/FIXES.md", json_path: str = "docs/FIXES.json"):
    fixes = FixRegistry.discover()

    md_lines = [
        "Source values: core (built-in) or plugin:<package> (discovered plugin fix).",
        "",
        "| Code | Name | Description | Categories | Dataset | Priority | Source |",
        "|------|------|-------------|------------|---------|---------|--------|",
    ]
    json_list = []

    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        source = FixRegistry.source_label(f)
        md_lines.append(
            f"| {f.code} | {f.name} | {f.description} | {cats} | {f.dataset or ''} | {f.priority} | {source} |"
        )
        if hasattr(f, "model_dump"):
            entry = f.model_dump()
        else:
            entry = {
                "code": f.code,
                "name": f.name,
                "description": f.description,
                "categories": getattr(f, "categories", []) or [],
                "dataset": f.dataset,
                "priority": f.priority,
            }
        if isinstance(f, GroupFix) and f.member_codes:
            entry["member_codes"] = f.member_codes
        entry["source"] = source
        json_list.append(entry)

    Path(md_path).write_text("\n".join(md_lines), encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2), encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(fixes)} fixes")


if __name__ == "__main__":
    generate_catalog()
