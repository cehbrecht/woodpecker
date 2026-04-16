from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry


def main():
    fixes = FixRegistry.discover()
    fix_dicts = []
    for fix in fixes:
        entry = fix.model_dump() if hasattr(fix, "model_dump") else dict(fix.__dict__)
        entry["source"] = FixRegistry.source_label(fix)
        fix_dicts.append(entry)

    env = Environment(loader=FileSystemLoader("scripts/templates"), autoescape=True)
    template = env.get_template("fixes.html.jinja")

    html = template.render(fixes=fix_dicts)
    Path("docs/fixes.html").write_text(html, encoding="utf-8")
    print(f"Generated docs/fixes.html with {len(fixes)} fixes")


if __name__ == "__main__":
    main()
