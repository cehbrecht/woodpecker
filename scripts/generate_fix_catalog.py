from __future__ import annotations

import json
from pathlib import Path

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry, GroupFix


def generate_catalog(md_path: str = "docs/FIXES.md", json_path: str = "docs/FIXES.json"):
    fixes = FixRegistry.discover()

    md_lines = ["Source values: core (built-in) or plugin:<package> (discovered plugin fix).", ""]
    json_list = []
    grouped_rows: dict[str, list[tuple[str, str, str, str, str, int, str]]] = {"core": []}

    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        source = FixRegistry.source_label(f)
        row = (f.canonical_id, f.name, f.description, cats, f.dataset or "", f.priority, source)
        if source == "core":
            grouped_rows["core"].append(row)
        else:
            grouped_rows.setdefault(source, []).append(row)

        entry = {
            "id": f.canonical_id,
            "local_id": getattr(f, "local_id", ""),
            "namespace": getattr(f, "namespace_prefix", ""),
            "aliases": list(getattr(f, "aliases", []) or []),
            "name": f.name,
            "description": f.description,
            "categories": getattr(f, "categories", []) or [],
            "dataset": f.dataset,
            "priority": f.priority,
        }
        if isinstance(f, GroupFix) and getattr(f, "members", None):
            entry["member_ids"] = [
                getattr(member, "canonical_id", "") or getattr(member, "local_id", "")
                for member in f.members
            ]
        entry["source"] = source
        json_list.append(entry)

    ordered_group_keys = ["core"] + sorted(key for key in grouped_rows.keys() if key != "core")
    for key in ordered_group_keys:
        rows = grouped_rows.get(key, [])
        if not rows:
            continue
        heading = "## Core" if key == "core" else f"## Plugin: {key.split(':', 1)[1]}"
        md_lines.extend(
            [
                heading,
                "",
                "| ID | Name | Description | Categories | Dataset | Priority | Source |",
                "|----|------|-------------|------------|---------|---------|--------|",
            ]
        )
        for fix_id, name, description, cats, dataset, priority, source in rows:
            md_lines.append(
                f"| {fix_id} | {name} | {description} | {cats} | {dataset} | {priority} | {source} |"
            )
        md_lines.append("")

    Path(md_path).write_text("\n".join(md_lines), encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2), encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(fixes)} fixes")


if __name__ == "__main__":
    generate_catalog()
