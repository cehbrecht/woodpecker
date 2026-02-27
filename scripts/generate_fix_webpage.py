from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Import fixes to ensure registration
import woodpecker.fixes  # noqa: F401
from woodpecker.fixes.registry import FixRegistry


def main():
    fixes = FixRegistry.discover()
    fix_dicts = [
        (f.model_dump() if hasattr(f, "model_dump") else f.__dict__)
        for f in fixes
    ]

    env = Environment(loader=FileSystemLoader("scripts/templates"), autoescape=True)
    template = env.get_template("fixes.html.jinja")

    html = template.render(fixes=fix_dicts)
    Path("docs/fixes.html").write_text(html, encoding="utf-8")
    print(f"Generated docs/fixes.html with {len(fixes)} fixes")


if __name__ == "__main__":
    main()
