#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen.py — sets the README of github.com/L0stInFades.

Black, white, and a great deal of air: the name in a thin, widely spaced sans, titles in
a classical serif, small tracked capitals, a hairline here and there. The manner of a
quiet hotel's stationery. One thing is done to the name and to nothing else: of its five
A's only the first is whole, and the rest are echoes of it (see `echoes`).

    python3 gen.py              # needs:  pip install fonttools brotli

GitHub allows no CSS in a README, so every block is a self-contained SVG "plate" with its
type embedded (Jost · Cormorant Garamond · Inter, all OFL, subset per plate to the glyphs
it uses). The plates do two things a plain picture cannot:

  * They are fluid. A plate has a height but no viewBox, so it is never scaled. It is set
    four times (desktop, tablet, phone, small phone) and a media query inside the SVG
    shows the setting that fits the width it is given, so type stays the size it was set at.
  * They follow the theme. The hero is black in any light; every other plate is drawn
    twice, and <picture> hands GitHub the ink that suits the reader's theme.

Each face has one job: Jost for the name, Cormorant Garamond for titles, figures and
anything literary, Inter for labels and plain facts.

To change the page, edit the copy below (NAME … COLOPHON) and run this again.
`python3 gen.py --heights` also prints the height each setting asked of each plate.

The contributions are not drawn here: ledger.py sets the figures, tint.py re-inks the 3D
graph, and both are run daily by .github/workflows.
"""
import base64
import html
import os
import sys
from io import BytesIO
from types import SimpleNamespace as NS

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
README = os.path.join(ROOT, "README.md")
ASSET_PREFIX = "assets/readme/"

# ── the copy ────────────────────────────────────────────────────────────────
NAME = "Raaaaaymond"
HANDLE = "L0stInFades"
SINCE = "Est. MMXXIV"
ROLE = "of systems, engines, proofs & music"
PROFILE_URL = "https://github.com/" + HANDLE

EPIGRAPH = ["Of systems that think, and music that computes;",
            "of proofs wherein words fall silent;",
            "of engines for worlds not yet rendered;",
            "of compression, as a manner of meditation;",
            "and of compilers written for the unnameable."]

STATEMENT = ("I labour at the margins of computing: in the building of engines for games, the verification "
             "of mathematics, and the composing of algorithms into music. Each undertaking is an endeavour "
             "to find that precise language which a problem deserves.")

SECTIONS = ["Of Present Labours", "A Catalogue of Selected Works",
            "Of the Instruments", "A Chronicle of Contributions"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# I · what is on the bench at present
NOW = NS(name="edyt.video", url="https://edyt.video", status="In early access", door="Visit the site",
         line="An editor for motion design: clean, ready-to-ship animations, without the customary complexity.",
         text="smooth pathing upon curves · the morphing of shapes\na camera system · staggered reveals")

# II · name as shown · where it lives · repository · a line of portrait · what it is \n what it is made of
DOOR = "Discover"
WORKS = [
    NS(name="Afterglow", place="Windows", repo="Afterglow",
       line="The light that lingers after the moment has passed.",
       text="An image viewer in the manner of iOS Photos.\nC++, Direct2D, DirectComposition, spring physics."),
    NS(name="Vien", place="macOS", repo="vien",
       line="Calm Markdown for long stretches of attention.",
       text="A native editor, in Swift alone.\nNo Electron, no WebKit, no dependencies."),
    NS(name="Lector", place="Android", repo="echo-read",
       line="Tap any word, and the reading begins there.",
       text="An AI audiobook reader for TXT and EPUB.\nKotlin, Jetpack Compose, Media3."),
    NS(name="Unfold", place="macOS", repo="Unfold",
       line="Unfold, gently.",
       text="A small, native archive app.\nSwift, AppKit, Metal."),
]

# III
STACK = ["C++", "Rust", "TypeScript", "Python", "OCaml", "Lean 4",
         "Verilog", "Gleam", "SuperCollider", "Electron", "Linux", "Vim"]

# IV · drawn elsewhere (see the docstring); these are where the drawings are kept
CONTRIB3D = "profile-3d-contrib/profile-{theme}.svg"
SNAKE = "https://raw.githubusercontent.com/L0stInFades/L0stInFades/output/snake-{theme}.svg"

COLOPHON = ("This page was set in Jost, Cormorant Garamond & Inter;\n"
            "the plates were drawn by assets/readme/gen.py, and the whole printed for the author.")
COLOPHON_MARK = "L0stInFades · MMXXVI"

# ── ink ─────────────────────────────────────────────────────────────────────
# Day is drawn on white, so a reader whose client ignores <picture> still gets a legible
# card; night is drawn on nothing and takes whichever dark GitHub is showing, which is
# why its hairline is a veil of white rather than a grey chosen for one of them.
DAY = NS(key="light", ground="#ffffff", ink="#000000", text="#4a4a4a", mute="#767676", hair=("#000000", .11))
NIGHT = NS(key="dark", ground=None, ink="#ffffff", text="#b8b8b8", mute="#949494", hair=("#ffffff", .15))
THEMES = (DAY, NIGHT)
HERO = NS(ground="#000000", ink="#ffffff", mute="#8c8c8c")

# ── the four settings ───────────────────────────────────────────────────────
# `fits` is the narrowest plate a setting may be shown in. A profile README is about
# 850 px wide on a desktop, 280 to 350 on a phone, and 238 on the smallest phone made.
# `air` scales the room above and below a column; `side` is the room beside the name and
# `spread` its letter-spacing; the rest are type sizes.
SET = {
    "w": NS(fits=720, margin=38, side=60, spread=.34, mark=50, title=58, verse=23.0, ital=21.5, prose=20.5,
            text=14.0, caps=10.5, figure=58, measure=560, air=1.00),
    "m": NS(fits=460, margin=28, side=28, spread=.34, mark=40, title=48, verse=21.5, ital=20.5, prose=19.5,
            text=14.0, caps=10.5, figure=46, measure=392, air=0.92),
    "n": NS(fits=290, margin=18, side=14, spread=.26, mark=30, title=38, verse=20.0, ital=19.5, prose=18.5,
            text=13.5, caps=10.0, figure=38, measure=262, air=0.80),
    "s": NS(fits=236, margin=14, side=10, spread=.20, mark=26, title=32, verse=18.5, ital=18.0, prose=17.5,
            text=13.0, caps=9.5, figure=32, measure=216, air=0.66),
}
# Desktop is the default; the narrower settings take over by media query, so a renderer
# that understands none of this still shows one complete page.
CSS_SETTINGS = (".m,.n,.s{display:none}"
                "@media (max-width:719.9px){.w{display:none}.m{display:inline}}"
                "@media (max-width:459.9px){.m{display:none}.n{display:inline}}"
                "@media (max-width:289.9px){.n{display:none}.s{display:inline}}")

TRACK = 0.26       # letter-spacing of the small capitals, in em
TITLE_TRACK = 0.1  # and of the serif titles
NBSP = chr(0xA0)   # a space that SVG text will not collapse


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def flat(s: str) -> str:
    """Copy with its line breaks taken out, for alt text."""
    return " ".join(s.split())


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
        self.cap = self.tt["OS/2"].sCapHeight / self.upem

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
        missing = sorted(c for c in chars if ord(c) not in self.cmap)
        if missing:
            raise SystemExit(f"{self.key} has no glyph for {missing!r}: add it in cut_fonts.py")
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "lnum"]
        opts.hinting = False
        opts.desubroutinize = True
        opts.notdef_outline = True
        opts.name_IDs = [1, 2]
        f = TTFont(self.path, recalcTimestamp=False)  # the same plate, byte for byte, on every run
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
    "name":   Font("jost-light",       "RdName"),    # the name, and nothing else
    "serif":  Font("cormorant",        "RdSerif"),   # titles, figures, the statement
    "italic": Font("cormorant-italic", "RdItalic"),  # the epigraph, the one-line portraits
    "light":  Font("inter-light",      "RdLight"),   # plain facts
    "caps":   Font("inter-regular",    "RdCaps"),    # small capitals
}

USED: dict = {}     # font key -> characters used by the plate being built
HEIGHTS: dict = {}  # plate -> the height each setting asked for (printed by --heights)


def use(font: str, s: str) -> None:
    USED.setdefault(font, set()).update(s)


def fit(font: str, text: str, max_w: float, max_size: float, track: float = 0.0) -> float:
    """Largest whole size ≤ max_size at which the text fits in max_w (`track` in em)."""
    return float(int(min(max_size, max_w / (F[font].width(text, 1.0, track) - track))))


def wrap(font: str, size: float, text: str, measure: float, track: float = 0.0, balance: bool = True):
    """Break into centred lines no wider than `measure`, then even the lines out so the
    last is never a stray word. A newline in the copy is a break that always holds."""
    if "\n" in text:
        return [ln for part in text.split("\n") for ln in wrap(font, size, part, measure, track, balance)]
    words = text.split()

    def greedy(limit):
        lines, cur = [], []
        for w in words:
            if cur and F[font].width(" ".join(cur + [w]), size, track * size) > limit:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur = cur + [w]
        return lines + [" ".join(cur)] if cur else lines

    lines = greedy(measure)
    if balance and len(lines) > 1:
        lo, hi = 0.0, measure
        for _ in range(20):
            mid = (lo + hi) / 2
            if len(greedy(mid)) <= len(lines):
                hi = mid
            else:
                lo = mid
        lines = greedy(hi)
    return lines


DOT = " · "


def facts(font: str, size: float, text: str, measure: float):
    """Running facts. Where they are a list joined by middle dots, break between the things
    listed, so that no line begins or ends on a dot."""
    out = []
    for part in text.split("\n"):
        out += rows(part.split(DOT), font, size, measure, 0.0, DOT) if DOT in part else wrap(font, size, part, measure)
    return out


def rows(items, font: str, size: float, measure: float, track: float, gap: str):
    """Flow a list of words into centred rows, as few as will fit, as even as they will go."""
    def greedy(limit):
        out, cur = [], []
        for it in items:
            if cur and F[font].width(gap.join(cur + [it]), size, track * size) > limit:
                out.append(cur)
                cur = [it]
            else:
                cur = cur + [it]
        return out + [cur] if cur else out

    best = greedy(measure)
    lo, hi = 0.0, measure
    for _ in range(20):
        mid = (lo + hi) / 2
        if len(greedy(mid)) <= len(best):
            hi = mid
        else:
            lo = mid
    return [gap.join(r) for r in greedy(hi)]


# ── primitives ──────────────────────────────────────────────────────────────
# Nothing is positioned in absolute x: a plate may be 240 px wide or 900. Text hangs from
# the left edge (a number), a share of the width ("50%") or the right edge ("100%"),
# nudged by dx.
def T(x, y, s, font, size, fill, anchor="middle", track=0.0, dx=0.0, lining=False) -> str:
    """`lining` asks for figures that stand as tall as capitals (Cormorant's are old-style
    by default, and its old-style 1 reads as a small capital I)."""
    use(font, s)
    ls = track * size
    # browsers count the letter-spacing after the last glyph in the anchored advance
    shift = dx + (ls / 2 if anchor == "middle" else ls if anchor == "end" else 0.0)
    a = [f'x="{x}"', f'y="{y:.1f}"', f'font-family="{F[font].family}"',
         f'font-size="{size:g}"', f'fill="{fill}"']
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls:.2f}"')
    if abs(shift) > 0.005:
        a.append(f'dx="{shift:.2f}"')
    if lining:
        a.append("style=\"font-feature-settings:'lnum'\"")
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def hairline(y, hair) -> str:
    """Edge to edge. `hair` is (colour, opacity)."""
    return f'<rect y="{y:g}" width="100%" height="1" fill="{hair[0]}" fill-opacity="{hair[1]:g}"/>'


def upright(x, y, h, hair) -> str:
    """A vertical hairline at a share of the width."""
    return f'<rect x="{x}" y="{y:g}" width="1" height="{h:g}" fill="{hair[0]}" fill-opacity="{hair[1]:g}"/>'


def centred_rect(y, w, h, attrs) -> str:
    return (f'<rect x="50%" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'transform="translate({-w / 2:g} 0)" {attrs}/>')


def dash(y, t, w=28) -> str:
    """A short rule in the middle: the pause between two things of the same kind."""
    return centred_rect(y, w, 1, f'fill="{t.mute}"')


def plaque(y, label, w, h, ink, size=10.5, track=TRACK) -> str:
    """A sharp-cornered rectangle drawn in outline, with a word in it: a door."""
    box = centred_rect(y + .5, w - 1, h - 1, f'fill="none" stroke="{ink}" shape-rendering="crispEdges"')
    return box + T("50%", y + h / 2 + F["caps"].cap * size / 2, label.upper(), "caps", size, ink, track=track)


def plaque_width(label, size, track=TRACK, pad=28) -> float:
    return float(int(F["caps"].width(label.upper(), size, track * size) - track * size + 2 * pad + 1) // 2 * 2)


class Column:
    """Lines stacked down the middle of a plate. `y` is always the last baseline, and a
    gap is measured from there to the top of the next capitals."""

    def __init__(self):
        self.y, self.b = 0.0, []

    def gap(self, h):
        self.y += h
        return self

    def lines(self, lines, font, size, fill, leading, track=0.0, upper=False):
        self.y += F[font].cap * size
        for i, ln in enumerate(lines):
            self.y += leading if i else 0
            self.b.append(T("50%", self.y, ln.upper() if upper else ln, font, size, fill, track=track))
        return self

    def caps(self, s, size, fill, track=TRACK, measure=None):
        """Small capitals; given a measure they wrap."""
        lines = wrap("caps", size, s.upper(), measure, track) if measure else [s]
        return self.lines(lines, "caps", size, fill, size * 1.9, track, upper=True)

    def title(self, s, size, fill):
        return self.lines([s], "serif", size, fill, 0, TITLE_TRACK, upper=True)

    def add(self, markup, h):
        """`markup` is a callable taking the y of its top edge."""
        self.b.append(markup(self.y))
        self.y += h
        return self


def plate(settings: dict, title: str, ground=None, rules: str = "", css: str = "", pad=(0, 0)) -> str:
    """The same column in each setting, in one fixed height (an <img> cannot change its
    height by media query): the tallest setting decides, the others share out the slack.
    `settings` maps "w"/"m"/"n"/"s" to a Column (or to (markup, height)); `pad` is the
    room above and below at full air."""
    done = {k: ("".join(v.b), v.y) if isinstance(v, Column) else v for k, v in settings.items()}
    need = {k: height + (pad[0] + pad[1]) * SET[k].air for k, (_, height) in done.items()}
    h = int(round(max(need.values())))
    HEIGHTS[title] = {k: round(v) for k, v in need.items()}
    body = []
    for k, (markup, height) in done.items():
        top = pad[0] * SET[k].air + (h - need[k]) / 2
        body.append(f'<g class="{k}" transform="translate(0 {top:.1f})">{markup}</g>')
    faces = "".join(F[k].face_for("".join(sorted(USED[k]))) for k in F if USED.get(k))
    USED.clear()
    bg = f'<rect width="100%" height="100%" fill="{ground}"/>' if ground else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="{h}" role="img" '
            f'aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<style>{faces}{CSS_SETTINGS}{css}</style>{bg}{rules}{"".join(body)}</svg>')


# ── the plates ──────────────────────────────────────────────────────────────
HERO_H = 420
ECHO = (.80, .60, .44, .30)  # what is left of each A after the first
HERO_CSS = ("@keyframes f{from{opacity:0}}"
            ".f1{animation:f 1.4s cubic-bezier(.3,.1,.3,1) both}"
            ".f2{animation:f 1.2s .45s ease-out both}"
            ".f3{animation:f 1.2s .8s ease-out both}"
            + "".join(f".e{i + 1}{{animation:f 1.1s {.6 + .25 * i:.2f}s ease-out both}}" for i in range(len(ECHO)))
            + "@media (prefers-reduced-motion:reduce){.f1,.f2,.f3,"
            + ",".join(f".e{i + 1}" for i in range(len(ECHO))) + "{animation:none}}")
HERO_ALT = f"{NAME} ({HANDLE}), {ROLE}."


def echoes(word: str):
    """The one thing done to the name. In a run of A's the first is whole and each one after
    it is an echo: -> [(letter, None or how much of it is left)]."""
    out, run = [], 0
    for ch in word.upper():
        run = run + 1 if ch == "A" and out and out[-1][0] == "A" else 0
        out.append((ch, ECHO[min(run, len(ECHO)) - 1] if run else None))
    return out


def set_name(size: float, spread: float):
    """Place the name letter by letter. An echo is drawn with a V stood on its head, which is
    an A that has lost its bar. -> ([(glyph, x from the left, echo)], width)"""
    x, placed = 0.0, []
    for ch, echo in echoes(NAME):
        glyph = "V" if echo else ch
        placed.append((glyph, x, echo))
        x += F["name"].width(glyph, size) + spread * size
    return placed, x - spread * size


def name_mark(y: float, size: float, spread: float) -> str:
    """The name, centred, its baseline at y: the letters fade in together, then the echoes
    arrive one after another, each fainter than the last."""
    f = F["name"]
    cap = f.cap * size
    placed, width = set_name(size, spread)
    out, n = [], 0
    for glyph, x, echo in placed:
        use("name", glyph)
        at = (f'x="50%" y="{y:.1f}" dx="{x - width / 2:.2f}" font-family="{f.family}" '
              f'font-size="{size:g}" fill="{HERO.ink}"')
        if echo:
            n += 1
            # mirrored about the middle of the capitals; x is untouched, so "50%" still holds
            out.append(f'<text class="e{n}" {at} fill-opacity="{echo:g}" '
                       f'transform="translate(0 {2 * y - cap:.2f}) scale(1 -1)">{glyph}</text>')
        else:
            out.append(f'<text class="f1" {at}>{glyph}</text>')
    return "".join(out)


def hero() -> str:
    """Night, whatever the hour: the name, alone, in the middle of a black room."""
    out = {}
    for k, s in SET.items():
        H, side, b = HERO_H, s.margin, []
        cap_small = F["caps"].cap * s.caps
        # the two corners
        b.append('<g class="f3">'
                 + T(side, side + cap_small, HANDLE.upper(), "caps", s.caps, HERO.ink, "start", track=TRACK)
                 + T("100%", side + cap_small, SINCE.upper(), "caps", s.caps, HERO.ink, "end", track=TRACK, dx=-side)
                 + '</g>')
        # the name, and under it what the name is for
        size = float(int(min(s.mark, (s.fits - 2 * s.side) / set_name(1.0, s.spread)[1])))
        cap = F["name"].cap * size
        role = wrap("caps", s.caps, ROLE.upper(), s.fits - 2 * side, TRACK)
        under, lead = (30 if k in "wm" else 24), s.caps * 2
        block = cap + under + cap_small + lead * (len(role) - 1)
        top = (H - block) / 2 - 4
        b.append(name_mark(top + cap, size, s.spread))
        b.append('<g class="f2">' + "".join(
            T("50%", top + cap + under + cap_small + i * lead, ln, "caps", s.caps, HERO.mute, track=TRACK)
            for i, ln in enumerate(role)) + '</g>')
        out[k] = ("".join(b), H)
    return plate(out, HERO_ALT, ground=HERO.ground, css=HERO_CSS)


EPIGRAPH_ALT = " ".join(EPIGRAPH)


def epigraph(t) -> str:
    out = {}
    for k, s in SET.items():
        c = Column()
        for i, verse in enumerate(EPIGRAPH):
            c.gap(s.verse * (.92 if i else 0))
            c.lines(wrap("italic", s.verse, verse, s.measure), "italic", s.verse, t.ink, s.verse * 1.3)
        out[k] = c
    return plate(out, EPIGRAPH_ALT, ground=t.ground, pad=(76, 44))


def statement(t) -> str:
    out = {}
    for k, s in SET.items():
        c = Column().add(lambda y: dash(y, t), 1)
        c.gap(42).lines(wrap("serif", s.prose, STATEMENT, min(s.measure, 540), balance=False),
                        "serif", s.prose, t.ink, s.prose * 1.5)
        out[k] = c
    return plate(out, STATEMENT, ground=t.ground, pad=(0, 84))


def section_alt(n: int) -> str:
    return f"{ROMAN[n - 1]} · {SECTIONS[n - 1]}"


def section(n: int, t) -> str:
    """A numeral, and under it what the part is called."""
    out = {}
    for k, s in SET.items():
        c = Column().lines([ROMAN[n - 1]], "italic", s.verse + 4, t.mute, 0)
        c.gap(20).caps(SECTIONS[n - 1], s.caps + .5, t.ink, track=.3, measure=s.measure)
        out[k] = c
    return plate(out, section_alt(n), ground=t.ground, rules=hairline(0, t.hair), pad=(66, 0))


def entry(label, name, line, text, door, t, first=True) -> dict:
    """One thing, set the way a hotel sets a city: where, the name, a line, a door."""
    out = {}
    for k, s in SET.items():
        c = Column()
        if not first:
            c.add(lambda y: dash(y, t), 1).gap(52 * s.air)
        c.caps(label, s.caps, t.mute)
        size = fit("serif", name.upper(), s.measure, s.title, TITLE_TRACK)
        c.gap(size * .5).title(name, size, t.ink)
        c.gap(size * .44).lines(wrap("italic", s.ital, line, s.measure), "italic", s.ital, t.ink, s.ital * 1.3)
        c.gap(18).lines(facts("light", s.text, text, s.measure), "light", s.text, t.text, s.text * 1.62)
        dw = plaque_width(door, s.caps)
        c.gap(30).add(lambda y: plaque(y, door, dw, 38, t.ink, size=s.caps), 38)
        out[k] = c
    return out


NOW_ALT = f"{NOW.name}, {NOW.status.lower()}. {NOW.line} " + NOW.text.replace("\n", " · ")


def now(t) -> str:
    return plate(entry(NOW.status, NOW.name, NOW.line, NOW.text, NOW.door, t),
                 NOW_ALT, ground=t.ground, pad=(46, 70))


def work_alt(p) -> str:
    return flat(f"{p.name}, for {p.place}. {p.line} {p.text}")


def work(i: int, p, t) -> str:
    label = f"{i + 1:02d}{NBSP * 2}—{NBSP * 2}{p.place}"
    last = i == len(WORKS) - 1
    return plate(entry(label, p.name, p.line, p.text, DOOR, t, first=i == 0),
                 work_alt(p), ground=t.ground, pad=(46 if i == 0 else 0, 70 if last else 52))


INSTRUMENTS_ALT = "Instruments: " + ", ".join(STACK)


def instruments(t) -> str:
    out = {}
    for k, s in SET.items():
        size = s.caps + .5
        stack = [name.upper() for name in STACK]   # measured as they will be set
        room = s.fits - 2 * s.margin               # a list may run wider than prose
        c = Column().lines(rows(stack, "caps", size, room, TRACK, NBSP * (6 if k in "wm" else 4)),
                           "caps", size, t.ink, size * 3, TRACK)
        out[k] = c
    return plate(out, INSTRUMENTS_ALT, ground=t.ground, pad=(48, 72))


def ledger(t, figures, note: str) -> str:
    """Three figures abreast, or one under another where there is no room.
    `figures` is three of (figure, what it counts, [since when: long form, short form])."""
    out = {}
    for k, s in SET.items():
        b, size, sub = [], s.figure, s.ital - 4.5
        cap, cap_small = F["serif"].cap * size, F["caps"].cap * (s.caps - .5)
        if k in "wm":      # abreast, a hairline between
            col = s.fits / 3 - 24
            label_at = cap + 24 + cap_small
            labels = [wrap("caps", s.caps - .5, lab.upper(), col, TRACK) for _, lab, _ in figures]
            sub_at = label_at + (max(len(ls) for ls in labels) - 1) * s.caps * 1.8 + 24
            for x, (fig, _, when), ls in zip(("17%", "50%", "83%"), figures, labels):
                b.append(T(x, cap, fig, "serif", size, t.ink, lining=True))
                for i, ln in enumerate(ls):
                    b.append(T(x, label_at + i * s.caps * 1.8, ln, "caps", s.caps - .5, t.mute, track=TRACK))
                since = next((w for w in when if F["italic"].width(w, sub) <= col), when[-1])
                b.append(T(x, sub_at, since, "italic", sub, t.text))
            b += [upright(x, 0, sub_at + 4, t.hair) for x in ("33.5%", "66.5%")]
            y = sub_at
        else:              # one under another: the figure to the left of what it counts
            split, row = "36%", max(cap, 30) + 30
            for i, (fig, lab, when) in enumerate(figures):
                base = i * row + cap
                mid = base - cap / 2
                room = s.fits * .64 - 14 - s.margin
                b.append(T(split, base, fig, "serif", size, t.ink, "end", dx=-12, lining=True))
                b.append(T(split, mid - 5, lab.upper(), "caps", s.caps - 1, t.mute, "start", track=.2, dx=12))
                since = next((w for w in when if F["italic"].width(w, sub) <= room), when[-1])
                b.append(T(split, mid + 5 + sub * .62, since, "italic", sub, t.text, "start", dx=12))
            y = 2 * row + cap + 4
        y += 44 * s.air + cap_small
        b.append(T("50%", y, note.upper(), "caps", s.caps - 1, t.mute, track=TRACK))
        out[k] = ("".join(b), y)
    title = " · ".join(f"{fig} {lab}" for fig, lab, _ in figures)
    return plate(out, title, ground=t.ground, pad=(52, 52))


COLOPHON_ALT = f"{flat(COLOPHON)} {COLOPHON_MARK}"


def colophon(t) -> str:
    out = {}
    for k, s in SET.items():
        size = s.ital - 4
        c = Column().lines(wrap("italic", size, COLOPHON, s.measure), "italic", size, t.text, size * 1.5)
        c.gap(30).caps(COLOPHON_MARK, s.caps - .5, t.ink)
        out[k] = c
    return plate(out, COLOPHON_ALT, ground=t.ground, rules=hairline(0, t.hair), pad=(56, 44))


# ── README ──────────────────────────────────────────────────────────────────
def img(src: str, alt: str) -> str:
    return f'<img src="{src}" alt="{esc(alt)}" width="100%" align="top">'


def themed(pattern: str, alt: str) -> str:
    """`pattern` has a {theme} in it: the light drawing is the fallback, the dark one a <source>."""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{pattern.format(theme="dark")}">'
            f'{img(pattern.format(theme="light"), alt)}</picture>')


def link(href: str, inner: str) -> str:
    return f'<a href="{href}">{inner}</a>'


def build():
    """-> ({file name: svg}, README text)"""
    files = {"hero.svg": hero()}
    out = [link(PROFILE_URL, img(ASSET_PREFIX + "hero.svg", HERO_ALT))]

    def both(stem, draw, alt, href):
        for t in THEMES:
            files[f"{stem}-{t.key}.svg"] = draw(t)
        out.append(link(href, themed(ASSET_PREFIX + stem + "-{theme}.svg", alt)))

    both("epigraph", epigraph, EPIGRAPH_ALT, PROFILE_URL)
    both("statement", statement, STATEMENT, PROFILE_URL)
    both("sec-1", lambda t: section(1, t), section_alt(1), NOW.url)
    both("now-edyt", now, NOW_ALT, NOW.url)
    both("sec-2", lambda t: section(2, t), section_alt(2), PROFILE_URL + "?tab=repositories")
    for i, p in enumerate(WORKS):
        both(f"work-{i + 1:02d}-{p.name.lower()}", lambda t, i=i, p=p: work(i, p, t),
             work_alt(p), f"{PROFILE_URL}/{p.repo}")
    both("sec-3", lambda t: section(3, t), section_alt(3), PROFILE_URL)
    both("instruments", instruments, INSTRUMENTS_ALT, PROFILE_URL)
    both("sec-4", lambda t: section(4, t), section_alt(4), PROFILE_URL)
    # set by ledger.py, tint.py and the snake workflow; only placed here
    out.append(link(PROFILE_URL, themed(ASSET_PREFIX + "ledger-{theme}.svg", "Contributions and streaks")))
    out.append(link(PROFILE_URL, themed(CONTRIB3D, "3D contribution graph")))
    out.append(link(PROFILE_URL, themed(SNAKE, "contribution snake")))
    both("colophon", colophon, COLOPHON_ALT, PROFILE_URL)
    text = "\n".join(['<!-- set by assets/readme/gen.py — edit that, not this -->',
                      '<div align="center">', *out, '</div>']) + "\n"
    return files, text


def main():
    files, text = build()
    if "--heights" in sys.argv:
        for title, need in HEIGHTS.items():
            print(f"  {title[:34]:34s} {need}")
    total = 0
    for fname, content in files.items():
        with open(os.path.join(HERE, fname), "w", encoding="utf-8") as fh:
            fh.write(content)
        total += len(content.encode())
        print(f"  {fname:28s} {len(content.encode()) / 1024:6.1f} KB")
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"  README.md  ->  {README}\n  total plates: {total / 1024:.0f} KB")


if __name__ == "__main__":
    main()
