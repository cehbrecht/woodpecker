from __future__ import annotations

from pathlib import Path
import json

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry


def generate_catalog(md_path: str = "docs/FIXES.md", json_path: str = "docs/FIXES.json"):
    fixes = FixRegistry.discover()

    md_lines = [
        "| Code | Name | Description | Categories | Dataset | Priority |",
        "|------|------|-------------|------------|---------|---------|",
    ]
    json_list = []

    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        md_lines.append(
            f"| {f.code} | {f.name} | {f.description} | {cats} | {f.dataset or ''} | {f.priority} |"
        )
        if hasattr(f, "model_dump"):
            json_list.append(f.model_dump())
        else:
            json_list.append({
                "code": f.code,
                "name": f.name,
                "description": f.description,
                "categories": getattr(f, "categories", []) or [],
                "dataset": f.dataset,
                "priority": f.priority,
            })

    Path(md_path).write_text("\n".join(md_lines), encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2), encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(fixes)} fixes")


if __name__ == "__main__":
    generate_catalog()
