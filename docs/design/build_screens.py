"""Builds docs/design/doc2all-screens.html from screens.src.html and the cat drawing (doc2all-cat.html).
Run: python -I docs/design/build_screens.py"""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
src = (root / "screens.src.html").read_text(encoding="utf-8")
cat_html = (root / "doc2all-cat.html").read_text(encoding="utf-8")

svg = re.search(r'<svg id="cat".*?</svg>', cat_html, re.S).group(0)
svg = svg.replace('id="cat"', 'class="cat"').replace('aria-label="A ginger cat holding a document"', 'aria-hidden="true"')
svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
svg = re.sub(r"\s*\n\s*", "", svg)

css = cat_html[cat_html.index("/* cat colours */"):cat_html.index("@media (max-width:760px)")]
css = css.replace("#cat ", ".cat ")

out = src.replace("%%CATCSS%%", css).replace("%%CATJS%%", json.dumps(svg))
(root / "doc2all-screens.html").write_text(out, encoding="utf-8")
print("built", len(out), "bytes")
