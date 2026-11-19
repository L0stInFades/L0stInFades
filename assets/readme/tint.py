#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tint.py — re-inks the generated 3D contribution graphs for the page: GitHub's language
colours become greys, the type becomes the page's own, and the night drawing loses its
ground, so that it sits on whichever dark GitHub is showing.

    python3 tint.py [profile-3d-contrib/profile-light.svg ...]     # default: both drawings

The drawings come from yoshi389111/github-profile-3d-contrib, which is given the page's
five tones in conf/3d-contrib.json; this only finishes what its settings cannot reach.
Needs:  pip install fonttools brotli   (it borrows a face from gen.py)
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen  # noqa: E402

DRAWINGS = [os.path.join(gen.ROOT, gen.CONTRIB3D.format(theme=t.key)) for t in gen.THEMES]

# the languages of the pie, from the most written to the least, and "other"
GREYS = {"light": ["#111111", "#555555", "#8a8a8a", "#b4b4b4", "#d4d4d4"],
         "dark":  ["#ffffff", "#b9bcc0", "#8a8e93", "#5f646a", "#444950"]}
OTHER = {"light": "#e6e6e6", "dark": "#30353c"}
MARK = "/*tinted*/"


def languages(svg: str, theme: str) -> str:
    """GitHub's language colours, in the order of the legend, become the page's greys."""
    seen = []
    for c in re.findall(r'<rect[^>]*width="21\.6[^"]*"[^>]*fill="(#[0-9a-fA-F]{6})"', svg):
        if c.lower() not in seen:
            seen.append(c.lower())
    for i, c in enumerate(seen):       # two passes, so a grey just laid down is never taken for a language
        svg = re.sub(re.escape(c), f"@@{i}@@", svg, flags=re.I)
    for i, c in enumerate(seen):
        tone = OTHER[theme] if c == "#444444" else GREYS[theme][min(i, len(GREYS[theme]) - 1)]
        svg = svg.replace(f"@@{i}@@", tone)
    return svg


def retype(svg: str) -> str:
    """Set the graph's words in the page's light grotesque, embedded like everything else."""
    face = gen.F["light"]
    words = html.unescape(re.sub(r"<[^>]+>", "", "".join(re.findall(r"<text[^>]*>(.*?)</text>", svg, flags=re.S))))
    have = "".join(sorted({c for c in words if ord(c) in face.cmap}))
    style = (f"<style>{MARK}{face.face_for(have)}"
             f"text{{font-family:'{face.family}','Helvetica Neue',Helvetica,Arial,sans-serif}}</style>")
    return re.sub(r"(<svg[^>]*>)", lambda m: m.group(1) + style, svg, count=1)


def unground(svg: str) -> str:
    """Take away the rectangle the whole drawing stands on."""
    return re.sub(r'<rect x="0" y="0" width="\d+" height="\d+" fill="[^"]*"></rect>', "", svg, count=1)


def tint(path: str) -> bool:
    theme = "dark" if path.endswith("-dark.svg") else "light"
    with open(path, encoding="utf-8") as fh:
        svg = fh.read()
    if MARK in svg:
        return False
    svg = retype(languages(svg, theme))
    if theme == "dark":
        svg = unground(svg)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return True


def main():
    for path in sys.argv[1:] or DRAWINGS:
        print(f"  {os.path.relpath(path, gen.ROOT)}: {'re-inked' if tint(path) else 'already re-inked'}")


if __name__ == "__main__":
    main()
