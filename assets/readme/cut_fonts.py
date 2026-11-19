#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cut_fonts.py — cuts the five static faces gen.py sets the README in, from the variable
sources published by Google Fonts (all three families are under the SIL Open Font License).

    python3 cut_fonts.py <dir holding the variable .ttf files>     # needs: fonttools brotli

Sources (github.com/google/fonts, ofl/jost, ofl/cormorantgaramond and ofl/inter):
    Jost[wght].ttf · CormorantGaramond[wght].ttf · CormorantGaramond-Italic[wght].ttf
    Inter[opsz,wght].ttf

Only run this to change a weight; the cut faces are checked in.
"""
import glob
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fonts")

# Latin, Latin-1, and the handful of dashes, quotes and arrows a page like this needs.
UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) +
            [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2032, 0x2033,
             0x2116, 0x2190, 0x2191, 0x2192, 0x2193, 0x2197, 0x2198, 0x25B2, 0x25BC])

#        file to write            source (glob)                      the instance
CUTS = [
    ("jost-light.woff2",       "Jost?wght*.ttf",                    {"wght": 300}),  # the name
    ("cormorant.woff2",        "CormorantGaramond?wght*.ttf",       {"wght": 500}),  # titles, figures, prose
    ("cormorant-italic.woff2", "CormorantGaramond-Italic?wght*.ttf", {"wght": 500}),  # the lines of portrait
    ("inter-light.woff2",      "Inter?opsz*.ttf",                   {"opsz": 14, "wght": 300}),  # running facts
    ("inter-regular.woff2",    "Inter?opsz*.ttf",                   {"opsz": 14, "wght": 400}),  # small capitals
]


def cut(src: str, dst: str, axes: dict) -> None:
    font = instancer.instantiateVariableFont(TTFont(src), axes, inplace=False)
    opts = subset.Options()
    # "lnum" is kept because Cormorant's figures are old-style unless a plate asks otherwise
    opts.layout_features = ["kern", "liga", "calt", "case", "lnum", "onum", "pnum", "locl", "ccmp", "mark"]
    opts.hinting = False
    opts.desubroutinize = True
    opts.notdef_outline = True
    opts.name_IDs = [0, 1, 2, 4, 6, 13, 14]  # keep the copyright and licence records
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    font.flavor = "woff2"
    font.save(dst)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    os.makedirs(OUT, exist_ok=True)
    for name, pattern, axes in CUTS:
        hits = [p for p in sorted(glob.glob(os.path.join(sys.argv[1], pattern)))
                if ("Italic" in os.path.basename(p)) == ("Italic" in pattern)]
        if not hits:
            raise SystemExit(f"no source matching {pattern} in {sys.argv[1]}")
        dst = os.path.join(OUT, name)
        cut(hits[0], dst, axes)
        print(f"  {name:24s} {os.path.getsize(dst) / 1024:5.1f} KB   {axes}")


if __name__ == "__main__":
    main()
