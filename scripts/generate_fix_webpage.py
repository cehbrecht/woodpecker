from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry


def main():
    fixes = FixRegistry.discover()
    fix_dicts = []
    core_count = 0
    plugin_count = 0
    plugin_packages: set[str] = set()

    for fix in fixes:
        entry = fix.model_dump() if hasattr(fix, "model_dump") else dict(fix.__dict__)
        source = FixRegistry.source_label(fix)
        source_kind = "core"
        source_package = ""
        if source.startswith("plugin:"):
            source_kind = "plugin"
            source_package = source.split(":", 1)[1]
            plugin_count += 1
            if source_package:
                plugin_packages.add(source_package)
        else:
            core_count += 1

        entry["source"] = source
        entry["source_kind"] = source_kind
        entry["source_package"] = source_package
        fix_dicts.append(entry)

    grouped: dict[str, list[dict]] = {"core": []}
    for entry in fix_dicts:
        if entry.get("source_kind") == "plugin":
            package = entry.get("source_package") or "unknown"
            grouped.setdefault(f"plugin:{package}", []).append(entry)
        else:
            grouped["core"].append(entry)

    group_sections: list[dict[str, object]] = []
    if grouped["core"]:
        group_sections.append(
            {
                "id": "core",
                "label": "Core",
                "kind": "core",
                "package": "",
                "count": len(grouped["core"]),
                "fixes": grouped["core"],
            }
        )

    plugin_group_keys = sorted(key for key in grouped.keys() if key.startswith("plugin:"))
    for key in plugin_group_keys:
        package = key.split(":", 1)[1]
        items = grouped[key]
        group_sections.append(
            {
                "id": key.replace(":", "-"),
                "label": f"Plugin: {package}",
                "kind": "plugin",
                "package": package,
                "count": len(items),
                "fixes": items,
            }
        )

    env = Environment(loader=FileSystemLoader("scripts/templates"), autoescape=True)
    template = env.get_template("fixes.html.jinja")

    html = template.render(
        fixes=fix_dicts,
        grouped_fixes=group_sections,
        total_count=len(fix_dicts),
        core_count=core_count,
        plugin_count=plugin_count,
        plugin_packages=sorted(plugin_packages),
    )
    Path("docs/fixes.html").write_text(html, encoding="utf-8")
    print(f"Generated docs/fixes.html with {len(fixes)} fixes")


if __name__ == "__main__":
    main()
