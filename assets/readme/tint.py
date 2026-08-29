#!/usr/bin/env python3
"""tint.py — re-inks the generated 3D contribution graph for the paper page:
GitHub's language colours become sepia, and the graph's text is set in a serif.

    python3 tint.py profile-3d-contrib/profile.svg
"""
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "profile-3d-contrib/profile.svg"
SEPIA = ["#5b4b36", "#8a7455", "#b39d78", "#cdbb98", "#ddd0b4"]
OTHER = "#a9a08d"

svg = open(PATH, encoding="utf-8").read()
legend = re.findall(r'<rect[^>]*width="21\.6[^"]*"[^>]*fill="(#[0-9a-fA-F]{6})"', svg)
seen = []
for c in legend:
    if c.lower() not in seen:
        seen.append(c.lower())
for i, c in enumerate(seen):
    tone = OTHER if c == "#444444" else SEPIA[min(i, len(SEPIA) - 1)]
    svg = re.sub(re.escape(c), tone, svg, flags=re.I)
svg = re.sub(r"(<svg[^>]*>)",
             r'\1<style>text{font-family:"EB Garamond",Garamond,Georgia,"Times New Roman",serif}</style>',
             svg, count=1)
open(PATH, "w", encoding="utf-8").write(svg)
print(f"tinted {len(seen)} language colours in {PATH}")
