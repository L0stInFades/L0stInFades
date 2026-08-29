#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen.py — sets the README of github.com/L0stInFades like a page from a well-made book:
ivory paper, Garamond, small capitals, roman numerals, dot leaders, a fleuron or two.

    python3 gen.py              # needs:  pip install fonttools brotli

GitHub allows no CSS in a README, so every block is a self-contained SVG "plate",
stacked edge to edge, with its type embedded (Cormorant Garamond · EB Garamond,
both OFL, subset per plate to the glyphs it actually uses).
"""
import base64
import html
import os
from io import BytesIO

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
README = os.path.join(ROOT, "README.md")
ASSET_PREFIX = "assets/readme/"

W = 900          # design width of every plate; GitHub scales them to the README column
L, R = 120, 780  # the text measure

# ── palette: paper and ink ──────────────────────────────────────────────────
PAPER = "#f4efe4"
INK = "#1f1c17"
INK2 = "#3d3831"     # running text
MUTED = "#7b7364"    # captions, small capitals
HAIR = "#cdc4b0"     # hairlines
HAIR2 = "#a59c89"
RUBRIC = "#8a3b2f"   # the one colour: numerals and ornaments

PROFILE_URL = "https://github.com/L0stInFades"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ── fonts ───────────────────────────────────────────────────────────────────
class Font:
    """An embedded woff2 subset + a small metrics engine (advances + GPOS kerning)
    so the layout can measure text without a browser."""

    def __init__(self, key: str, family: str):
        self.key, self.family = key, family
        self.path = os.path.join(FONT_DIR, key + ".woff2")
        self.tt = TTFont(self.path)
        self.upem = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"].metrics
        self.pairs = self._pair_subtables()
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0) / self.upem or 0.65

    def _pair_subtables(self):
        out = []
        if "GPOS" not in self.tt:
            return out
        gpos = self.tt["GPOS"].table
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        for li in sorted(idx):
            lk = gpos.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if type(st).__name__ == "PairPos":
                    out.append(st)
        return out

    def _kern(self, g1, g2):
        for st in self.pairs:
            cov = st.Coverage.glyphs
            if g1 not in cov:
                continue
            if st.Format == 1:
                for r in st.PairSet[cov.index(g1)].PairValueRecord:
                    if r.SecondGlyph == g2:
                        return getattr(r.Value1, "XAdvance", 0) or 0
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs.get(g1, 0)
                c2 = st.ClassDef2.classDefs.get(g2, 0)
                v = getattr(st.Class1Record[c1].Class2Record[c2].Value1, "XAdvance", 0) or 0
                if v:
                    return v
        return 0

    def has(self, ch: str) -> bool:
        return ord(ch) in self.cmap

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Advance width in px. `tracking` = CSS letter-spacing in px
        (browsers add it after every glyph, including the last)."""
        gl = [self.cmap.get(ord(c), ".notdef") for c in text]
        w = 0
        for i, g in enumerate(gl):
            w += self.hmtx.get(g, (0, 0))[0]
            if i + 1 < len(gl):
                w += self._kern(g, gl[i + 1])
        return w * size / self.upem + tracking * len(text)

    def face_for(self, chars: str) -> str:
        """@font-face carrying only the glyphs a single plate uses."""
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "lnum"]
        opts.hinting = False
        opts.desubroutinize = True
        opts.notdef_outline = True
        opts.name_IDs = [1, 2]
        f = TTFont(self.path)
        s = subset.Subsetter(opts)
        s.populate(unicodes=sorted({ord(c) for c in chars} | {0x20}))
        s.subset(f)
        f.flavor = "woff2"
        buf = BytesIO()
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return (f"@font-face{{font-family:'{self.family}';"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


F = {
    "display":  Font("cormorant-600",   "PgCormorant"),
    "displayi": Font("cormorant-i600",  "PgCormorantItalic"),
    "text":     Font("ebgaramond-400",  "PgGaramond"),
    "texti":    Font("ebgaramond-i400", "PgGaramondItalic"),
    "caps":     Font("ebgaramond-500",  "PgGaramondMedium"),
    "hand":     Font("pinyon-400",      "PgPinyon"),  # the copperplate hand: the signature
}

USED: dict = {}  # font key -> characters used by the plate being built


def use(font: str, s: str) -> None:
    USED.setdefault(font, set()).update(s)


def fit(font: str, text: str, max_w: float, max_size: float, tracking_em: float = 0.0) -> float:
    """Largest size ≤ max_size such that the text fits in max_w."""
    w1 = F[font].width(text, 1.0, tracking_em)
    return min(max_size, max_w / w1) if w1 else max_size


# ── shared defs: the paper ──────────────────────────────────────────────────
DEFS = """
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#000" stop-opacity=".055"/><stop offset=".08" stop-color="#000" stop-opacity="0"/>
  <stop offset=".92" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".055"/>
</linearGradient>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="11" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 .32  0 0 0 0 .26  0 0 0 0 .18  .045 .045 .045 0 0"/>
</filter>
"""


# ── primitives ──────────────────────────────────────────────────────────────
def svg(h: int, body: str, fonts, defs: str = "", title: str = "", w: int = W) -> str:
    style = "".join(F[k].face_for("".join(sorted(USED[k]))) for k in fonts if USED.get(k))
    USED.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title><style>{style}</style><defs>{DEFS}{defs}</defs>{body}</svg>')


def T(x, y, s, font, size, fill, anchor="start", tracking=0.0, extra="") -> str:
    use(font, s)
    if anchor == "middle":       # browsers count the trailing letter-spacing in the anchored advance
        x += tracking / 2
    elif anchor == "end":
        x += tracking
    ls = f' letter-spacing="{tracking:.2f}"' if tracking else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{F[font].family}" font-size="{size:.2f}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls} {extra}>{esc(s)}</text>')


def caps(x, y, s, size, fill, anchor="start", track=0.22, font="caps", extra="") -> str:
    """Letter-spaced capitals — the small-capital voice of the page."""
    return T(x, y, s.upper(), font, size, fill, anchor, tracking=track * size, extra=extra)


def caps_width(s, size, track=0.22, font="caps") -> float:
    return F[font].width(s.upper(), size, track * size)


def paper(h: int, w: int = W) -> str:
    return (f'<rect width="{w}" height="{h}" fill="{PAPER}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#edge)"/>'
            f'<rect width="{w}" height="{h}" filter="url(#grain)"/>')


def hairline(y, x0=L, x1=R, color=HAIR, width=1) -> str:
    return f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="{width}"/>'


def vline(x, y0, y1, color=HAIR, width=1) -> str:
    return f'<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="{width}"/>'


def double_rule(y, x0=L, x1=R, color=INK, thin_below=True) -> str:
    """The Oxford rule: a heavy line paired with a fine one."""
    a, b = (y, y + 4) if thin_below else (y + 4, y)
    return hairline(a, x0, x1, color, 1.6) + hairline(b, x0, x1, color, .6)


def fleuron(x, y, size=18, fill=RUBRIC) -> str:
    return T(x, y, "❦", "display", size, fill, anchor="middle")


def asterism(x, y, size=17, fill=RUBRIC) -> str:
    return T(x, y, "⁂", "display", size, fill, anchor="middle")


def leaders(x0, x1, y, color=HAIR2) -> str:
    """Dot leaders, as in a table of contents."""
    out, x = [], x0 + 4
    while x < x1 - 2:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r=".9" fill="{color}"/>')
        x += 8
    return "".join(out)


def wrap(font, size, words, measure, first_measure=None, n_first=0):
    lines, cur = [], []
    for w in words:
        limit = first_measure if (first_measure is not None and len(lines) < n_first) else measure
        trial = cur + [w]
        if cur and F[font].width(" ".join(trial), size) > limit:
            lines.append(cur)
            cur = [w]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def paragraph(text, font, size, leading, x, y, measure, fill=INK2, justify=True, drop=None,
              anchor="start"):
    """A justified paragraph (word-spacing per line). `drop=(font, lines)` sets the first
    letter as a drop capital spanning that many lines. Returns (svg, next_y)."""
    out, words = [], text.split()
    first_indent, n_first = 0, 0
    if drop:
        dfont, nl = drop
        ch, words[0] = words[0][0], words[0][1:]
        if not words[0]:
            words.pop(0)
        dsize = ((nl - 1) * leading + F[font].cap * size) / F[dfont].cap
        cw = F[dfont].width(ch, dsize)
        first_indent, n_first = cw + 14, nl
        out.append(T(x, y + (nl - 1) * leading, ch, dfont, dsize, INK))
    lines = wrap(font, size, words, measure, measure - first_indent, n_first)
    for i, ws in enumerate(lines):
        lx = x + first_indent if i < n_first else x
        lm = measure - first_indent if i < n_first else measure
        s = " ".join(ws)
        extra = ""
        if justify and i < len(lines) - 1 and len(ws) > 1:
            gap = lm - F[font].width(s, size)
            if 0 < gap < size * .7:
                extra = f'word-spacing="{gap / (len(ws) - 1):.2f}"'
        if anchor == "middle":
            out.append(T(x + measure / 2, y + i * leading, s, font, size, fill, anchor="middle"))
        else:
            out.append(T(lx, y + i * leading, s, font, size, fill, extra=extra))
    return "".join(out), y + len(lines) * leading


# ── the plates ──────────────────────────────────────────────────────────────
EPIGRAPH = ["Of systems that think, and music that computes;",
            "of proofs wherein words fall silent;",
            "of engines for worlds not yet rendered;",
            "of compression, as a manner of meditation;",
            "and of compilers written for the unnameable."]


def hero() -> str:
    h = 492
    b = [paper(h), double_rule(46)]
    b.append(caps(450, 80, "L0stInFades   ·   established MMXXIV", 10.5, MUTED, "middle", .3))
    name = "Raaaaaymond"
    size = fit("hand", name, 600, 100)
    b.append(T(450, 204, name, "hand", size, INK, anchor="middle"))
    role = "of systems, engines, proofs & music"
    rw = caps_width(role, 11, .28)
    b.append(caps(450, 276, role, 11, MUTED, "middle", .28))
    b.append(hairline(272, 450 - rw / 2 - 60, 450 - rw / 2 - 22, HAIR2))
    b.append(hairline(272, 450 + rw / 2 + 22, 450 + rw / 2 + 60, HAIR2))
    y = 330
    for line in EPIGRAPH:
        b.append(T(450, y, line, "texti", 18.5, INK2, anchor="middle"))
        y += 27
    b.append(asterism(450, y + 14))
    return svg(h, "".join(b), ["hand", "caps", "texti", "display"], "", "Raaaaaymond — L0stInFades")


STATEMENT = ("I labour at the margins of computing: in the building of engines for games, the verification "
             "of mathematics, and the composing of algorithms into music. Each undertaking is an endeavour "
             "to find that precise language which a problem deserves.")


def statement() -> str:
    body, end = paragraph(STATEMENT, "text", 18, 29, 170, 68, 560, drop=("display", 3))
    h = int(end + 30)
    return svg(h, paper(h) + body, ["text", "display"], "", STATEMENT)


def section(n: int, title: str) -> str:
    h = 110
    b = [paper(h)]
    b.append(T(450, 48, ROMAN[n - 1], "displayi", 27, RUBRIC, anchor="middle"))
    b.append(caps(450, 78, title, 13, INK, "middle", .32))
    b.append(hairline(93, 424, 476, HAIR2))
    return svg(h, "".join(b), ["displayi", "caps"], "", f"{ROMAN[n - 1]} · {title}")


def currently() -> str:
    h = 184
    b = [paper(h)]
    title = "edyt.video"
    b.append(T(L, 74, title, "displayi", 44, INK))
    b.append(caps(R, 70, "[ in early access ]", 10.5, RUBRIC, "end", .26))
    l1 = "An editor for motion design: clean, ready-to-ship animations, without the customary complexity."
    b.append(T(L, 108, l1, "text", fit("text", l1, R - L, 16), INK2))
    l2 = "smooth pathing upon curves · the morphing of shapes · a camera system · staggered reveals"
    b.append(T(L, 134, l2, "texti", fit("texti", l2, R - L, 14.5), MUTED))
    b.append(caps(R, 162, "visit the site  →", 10.5, MUTED, "end", .26))
    return svg(h, "".join(b), ["displayi", "caps", "text", "texti"], "",
               "edyt.video — an editor for motion design · in early access")


PROJECTS = [
    ("Afterglow", "an image viewer for Windows, after the manner of iOS Photos · Direct2D & DirectComposition · spring physics",
     "C++ · Direct2D", "https://github.com/L0stInFades/Afterglow"),
    ("ember", "RISC-V cores built from nothing, single-cycle to out-of-order · an RV32IMAC/Sv32 SoC that boots Linux to a shell",
     "Verilog · RISC-V", "https://github.com/L0stInFades/ember"),
    ("BlameEngine", "a headless engine of an authoritative world · UE5 view, Jolt physics · a sandbox wherein real code is the hack",
     "C++ · UE5 · Jolt", "https://github.com/L0stInFades/BlameEngine"),
    ("AnalysisTrinity", "formal proofs of Nested Intervals, Bolzano–Weierstrass & Heine–Borel — the trinity of completeness",
     "Lean 4", "https://github.com/L0stInFades/AnalysisTrinity"),
    ("nocturnes-in-code", "compositions by algorithm — neoclassical fugues, IDM drum machines, melodic techno, all synthesised from nothing",
     "SuperCollider", "https://github.com/L0stInFades/nocturnes-in-code"),
    ("Nevermind-Lang", "a language, of the author's own devising.",
     "Rust", "https://github.com/L0stInFades/Nevermind-Lang"),
    ("Quench", "compression as meditation · extraction as a gentle unfolding",
     "Rust", "https://github.com/L0stInFades/Quench"),
    ("Cocode-Precise", "an MCP server for the exact retrieval of code symbols — whole functions and classes, and nothing besides",
     "Python · MCP", "https://github.com/L0stInFades/Cocode-Precise"),
]


def work(i: int, name: str, desc: str, tag: str) -> str:
    """One entry of the table of contents."""
    h = 94
    b = [paper(h)]
    b.append(T(L, 42, ROMAN[i] + ".", "displayi", 16, RUBRIC))
    tx = 172
    b.append(T(tx, 42, name, "display", 29, INK))
    nw = F["display"].width(name, 29)
    tw = caps_width(tag, 10.5, .22)
    b.append(leaders(tx + nw + 12, R - tw - 12, 38))
    b.append(caps(R, 42, tag, 10.5, MUTED, "end", .22))
    ds = fit("texti", desc, R - tx, 14.5)
    b.append(T(tx, 67, desc, "texti", ds, INK2))
    return svg(h, "".join(b), ["displayi", "display", "caps", "texti"], "", f"{name} — {desc}")


STACK = ["C++", "Rust", "TypeScript", "Python", "OCaml", "Lean 4",
         "Verilog", "Gleam", "SuperCollider", "Electron", "Linux", "Vim"]


def instruments() -> str:
    h = 128
    b = [paper(h)]
    b.append(caps(450, 56, "   ·   ".join(STACK[:6]), 12, INK2, "middle", .26))
    b.append(caps(450, 90, "   ·   ".join(STACK[6:]), 12, INK2, "middle", .26))
    return svg(h, "".join(b), ["caps"], "", "Instruments: " + ", ".join(STACK))


def colophon() -> str:
    h = 198
    b = [paper(h), fleuron(450, 50, 20)]
    b.append(T(450, 88, "This page was set in Cormorant Garamond & EB Garamond, the name being written in Pinyon Script;",
               "texti", 14.5, INK2, anchor="middle"))
    b.append(T(450, 110, "the plates were drawn by assets/readme/gen.py, and the whole printed for the author.",
               "texti", 14.5, INK2, anchor="middle"))
    b.append(caps(450, 140, "L0stInFades   ·   MMXXVI", 10.5, MUTED, "middle", .3))
    b.append(double_rule(164, thin_below=False))
    return svg(h, "".join(b), ["display", "texti", "caps"], "", "Colophon — printed for the author, L0stInFades, 2026")


# ── README ──────────────────────────────────────────────────────────────────
def img(src, alt, width="100%"):
    return f'<img src="{src}" alt="{esc(alt)}" align="top" width="{width}">'


def link(href, inner):
    return f'<a href="{href}">{inner}</a>'


SNAKE = "https://raw.githubusercontent.com/L0stInFades/L0stInFades/output/snake.svg"
CONTRIB3D = "profile-3d-contrib/profile.svg"


def readme(rows):
    A = ASSET_PREFIX
    out = ['<!-- set by assets/readme/gen.py — edit that, not this -->', '<div align="center">']
    out.append(link(PROFILE_URL, img(A + "hero.svg", "Raaaaaymond — L0stInFades")))
    out.append(link(PROFILE_URL, img(A + "statement.svg", STATEMENT)))
    out.append(link("https://edyt.video", img(A + "sec-1.svg", "I · Of Present Labours")))
    out.append(link("https://edyt.video", img(A + "now-edyt.svg", "edyt.video — an editor for motion design · in early access")))
    out.append(link(PROFILE_URL + "?tab=repositories", img(A + "sec-2.svg", "II · A Catalogue of Selected Works")))
    for (name, desc, tag, url), fname in rows:
        out.append(link(url, img(A + fname, f"{name} — {desc}")))
    out.append(link(PROFILE_URL, img(A + "sec-3.svg", "III · Of the Instruments")))
    out.append(link(PROFILE_URL, img(A + "instruments.svg", "Instruments: " + ", ".join(STACK))))
    out.append(link(PROFILE_URL, img(A + "sec-4.svg", "IV · A Chronicle of Contributions")))
    out.append(link(PROFILE_URL, img(A + "ledger.svg", "Contributions and streaks")))
    out.append(link(PROFILE_URL, img(CONTRIB3D, "3D contribution graph")))
    out.append(link(PROFILE_URL, img(SNAKE, "contribution snake")))
    out.append(link(PROFILE_URL, img(A + "colophon.svg", "Colophon — printed for the author, L0stInFades, 2026")))
    out.append('</div>')
    return "\n".join(out) + "\n"


def main():
    files = {
        "hero.svg": hero(),
        "statement.svg": statement(),
        "sec-1.svg": section(1, "Of Present Labours"),
        "now-edyt.svg": currently(),
        "sec-2.svg": section(2, "A Catalogue of Selected Works"),
        "sec-3.svg": section(3, "Of the Instruments"),
        "instruments.svg": instruments(),
        "sec-4.svg": section(4, "A Chronicle of Contributions"),
        "colophon.svg": colophon(),
    }
    rows = []
    for i, p in enumerate(PROJECTS):
        fname = f"work-{i + 1:02d}-{p[0].lower()}.svg"
        files[fname] = work(i, p[0], p[1], p[2])
        rows.append((p, fname))
    total = 0
    for fname, content in files.items():
        with open(os.path.join(HERE, fname), "w", encoding="utf-8") as fh:
            fh.write(content)
        total += len(content.encode())
        print(f"  {fname:28s} {len(content.encode()) / 1024:6.1f} KB")
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(readme(rows))
    print(f"  README.md  ->  {README}\n  total plates: {total / 1024:.0f} KB")


if __name__ == "__main__":
    main()
