from __future__ import annotations

import json
from pathlib import Path

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.labels import FixLabelRegistry
from woodpecker.fixes.registry import FixFunctionRegistry


def generate_catalog(md_path: str = "docs/FIXES.md", json_path: str = "docs/FIXES.json"):
    fixes = FixFunctionRegistry.discover()

    md_lines = [
        "# Generated Fixes Reference",
        "",
        "This page is generated from registered core and plugin fixes.",
        "",
        "Source values: core (built-in) or plugin:<package> (discovered plugin fix).",
        "",
    ]
    json_list = []
    grouped_rows: dict[str, list[tuple[str, str, str, str, str, int, str, str, str]]] = {
        "core": []
    }

    for f in fixes:
        cats = ", ".join(getattr(f, "categories", []) or [])
        source = FixFunctionRegistry.source_label(f)
        risk = getattr(f, "risk", "")
        risk_label = FixLabelRegistry.title(risk)
        labels = list(getattr(f, "labels", []) or [])
        label_titles = [FixLabelRegistry.title(label) for label in labels]
        fix_id = f.id
        row = (
            fix_id,
            f.name,
            f.description,
            cats,
            f.dataset or "",
            f.priority,
            risk_label,
            ", ".join(label_titles),
            source,
        )
        if source == "core":
            grouped_rows["core"].append(row)
        else:
            grouped_rows.setdefault(source, []).append(row)

        entry = {
            "id": fix_id,
            "suffix": f.suffix,
            "prefix": f.prefix,
            "aliases": list(getattr(f, "aliases", []) or []),
            "name": f.name,
            "description": f.description,
            "categories": getattr(f, "categories", []) or [],
            "dataset": f.dataset,
            "priority": f.priority,
            "risk": risk,
            "risk_label": risk_label,
            "risk_metadata": FixLabelRegistry.metadata(risk),
            "labels": labels,
            "label_titles": label_titles,
            "label_metadata": [FixLabelRegistry.metadata(label) for label in labels],
        }
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
                "| ID | Name | Description | Categories | Dataset | Priority | Risk | Labels | Source |",
                "|----|------|-------------|------------|---------|---------|------|--------|--------|",
            ]
        )
        for fix_id, name, description, cats, dataset, priority, risk, labels, source in rows:
            md_lines.append(
                f"| {fix_id} | {name} | {description} | {cats} | {dataset} | {priority} | {risk} | {labels} | {source} |"
            )
        md_lines.append("")

    Path(md_path).write_text("\n".join(md_lines), encoding="utf-8")
    Path(json_path).write_text(json.dumps(json_list, indent=2), encoding="utf-8")
    print(f"Generated {md_path} and {json_path} with {len(fixes)} fixes")


if __name__ == "__main__":
    generate_catalog()
