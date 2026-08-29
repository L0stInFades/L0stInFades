#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen.py — builds the latex-aesthetic SVG assets (and README.md) for github.com/L0stInFades

    python3 gen.py              # needs:  pip install fonttools

Every visual lives in a self-contained SVG: gradients for the rubber sheen,
specular filters for the wet highlights, SMIL for the slow light sweep, and the
typefaces embedded as base64 woff2 subsets (Bodoni Moda · Montserrat · Inter ·
JetBrains Mono — all OFL). GitHub allows no CSS in READMEs, so the whole page
is composed from these plates, stacked edge-to-edge.
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
ASSET_PREFIX = "assets/latex/"

W = 900  # design width of every plate; GitHub scales them to the README column

# ── palette ─────────────────────────────────────────────────────────────────
INK = "#050505"     # the page: black latex
TXT = "#dadada"
SOFT = "#c3c3c3"
DIM = "#8a8a8a"
FAINT = "#4d4d4d"
HAIR = "#242424"
CR = "#ff2d55"      # crimson latex (lit)

PROFILE_URL = "https://github.com/L0stInFades"


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
        with open(self.path, "rb") as fh:
            self.b64 = base64.b64encode(fh.read()).decode()

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

    @property
    def face(self) -> str:
        return (f"@font-face{{font-family:'{self.family}';"
                f"src:url(data:font/woff2;base64,{self.b64}) format('woff2');}}")

    def face_for(self, chars: str) -> str:
        """@font-face carrying only the glyphs a single plate uses (keeps each SVG small)."""
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
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
    "name":  Font("bodoni-900",     "LXBodoniBlack"),
    "title": Font("bodoni-700",     "LXBodoniBold"),
    "ital":  Font("bodoni-i500",    "LXBodoniItalic"),
    "italb": Font("bodoni-i800",    "LXBodoniItalicBlack"),
    "label": Font("montserrat-600", "LXMont600"),
    "body":  Font("inter-400",      "LXInter"),
    "mono":  Font("jbmono-500",     "LXMono"),
}


def fit(font: str, text: str, max_w: float, max_size: float, tracking_em: float = 0.0) -> float:
    """Largest font size ≤ max_size such that the text fits in max_w."""
    w1 = F[font].width(text, 1.0, tracking_em)  # width at 1px (tracking scales with size)
    return min(max_size, max_w / w1) if w1 else max_size


USED: dict = {}  # font key -> set of characters used by the plate being built


def use(font: str, s: str) -> None:
    USED.setdefault(font, set()).update(s)


# ── shared defs ─────────────────────────────────────────────────────────────
DEFS = """
<linearGradient id="latex" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#121212"/><stop offset=".55" stop-color="#090909"/><stop offset="1" stop-color="#060606"/>
</linearGradient>
<radialGradient id="lamp" cx=".3" cy="0" r=".8">
  <stop offset="0" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</radialGradient>
<radialGradient id="vig" cx=".5" cy=".5" r=".72">
  <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".62"/>
</radialGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".075"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sheenS" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".32"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".45" stop-color="#fff" stop-opacity=".09"/>
  <stop offset=".5" stop-color="#fff" stop-opacity=".18"/><stop offset=".55" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".15" stop-color="#fff"/><stop offset=".85" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<linearGradient id="red" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ff8fa6"/><stop offset=".2" stop-color="#ff3f66"/><stop offset=".47" stop-color="#ec1a43"/>
  <stop offset=".53" stop-color="#ad0d33"/><stop offset="1" stop-color="#5f0a20"/>
</linearGradient>
<linearGradient id="spec" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#fff" stop-opacity=".62"/><stop offset=".13" stop-color="#fff" stop-opacity=".28"/>
  <stop offset=".3" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<linearGradient id="silver" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#b0b0b0"/>
</linearGradient>
<linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".42" stop-color="#dedede"/><stop offset=".5" stop-color="#8d8d8d"/>
  <stop offset=".58" stop-color="#d2d2d2"/><stop offset="1" stop-color="#f2f2f2"/>
</linearGradient>
<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".28" stop-color="#a3a3a3"/><stop offset=".5" stop-color="#f6f6f6"/>
  <stop offset=".72" stop-color="#4a4a4a"/><stop offset="1" stop-color="#d6d6d6"/>
</linearGradient>
<linearGradient id="ruleL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#161616"/><stop offset="1" stop-color="#5c5c5c"/></linearGradient>
<linearGradient id="ruleR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5c5c5c"/><stop offset="1" stop-color="#161616"/></linearGradient>
<linearGradient id="pill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#191919"/><stop offset="1" stop-color="#0a0a0a"/></linearGradient>
<linearGradient id="strap" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#222"/><stop offset=".5" stop-color="#0e0e0e"/><stop offset="1" stop-color="#070707"/>
</linearGradient>
<filter id="soft" x="-5%" y="-50%" width="110%" height="200%"><feGaussianBlur stdDeviation=".7"/></filter>
<filter id="soft2" x="-5%" y="-50%" width="110%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>
<filter id="soft4" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
"""


def rubber(fid: str, lx: float, ly: float, lz: float, blur: float = 2.2, scale: float = 5,
           k: float = .9, exp: float = 22) -> str:
    """Specular-lighting filter: turns flat fills into a puffy, wet, rubbery surface."""
    return (f'<filter id="{fid}" x="-10%" y="-25%" width="120%" height="150%">'
            f'<feGaussianBlur in="SourceAlpha" stdDeviation="{blur}" result="b"/>'
            f'<feSpecularLighting in="b" surfaceScale="{scale}" specularConstant="{k}" specularExponent="{exp}" '
            f'lighting-color="#fff" result="s"><fePointLight x="{lx}" y="{ly}" z="{lz}"/></feSpecularLighting>'
            f'<feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/>'
            f'<feComposite in="SourceGraphic" in2="s2" operator="arithmetic" k1="0" k2="1" k3="1" k4="0"/>'
            f'</filter>')


# ── primitives ──────────────────────────────────────────────────────────────
def svg(h: int, body: str, fonts, defs: str = "", title: str = "", w: int = W) -> str:
    style = "".join(F[k].face_for("".join(sorted(USED[k]))) for k in fonts if USED.get(k))
    USED.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title><style>{style}</style><defs>{DEFS}{defs}</defs>{body}</svg>')


def T(x, y, s, font, size, fill, anchor="start", tracking=0.0, extra="") -> str:
    use(font, s)
    # browsers include the trailing letter-spacing in the anchored advance — compensate
    if anchor == "middle":
        x += tracking / 2
    elif anchor == "end":
        x += tracking
    ls = f' letter-spacing="{tracking}"' if tracking else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{F[font].family}" font-size="{size:.2f}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls} {extra}>{esc(s)}</text>')


def plate(h: int, w: int = W) -> str:
    return f'<rect width="{w}" height="{h}" fill="{INK}"/><rect width="{w}" height="{h}" fill="url(#latex)"/>'


def seam(h: int, w: int = W) -> str:
    """A stitched edge: a dark groove and the lit ridge just beneath it."""
    return (f'<rect x="0" y="{h - 2}" width="{w}" height="1" fill="#000" fill-opacity=".65"/>'
            f'<rect x="0" y="{h - 1}" width="{w}" height="1" fill="#fff" fill-opacity=".06"/>')


def band(x, w, h, grad="sheen", op=1.0, skew=-22) -> str:
    """A diagonal sheen — light sliding across a curved rubber surface."""
    return (f'<rect x="{x}" y="-80" width="{w}" height="{h + 160}" fill="url(#{grad})" '
            f'opacity="{op}" transform="skewX({skew})"/>')


def arrow(x, y, color, s=1.0) -> str:
    """↗ drawn as a path so it never depends on glyph coverage."""
    return (f'<path d="M{x:.1f} {y + 8 * s:.1f} L{x + 8 * s:.1f} {y:.1f} M{x + 2.5 * s:.1f} {y:.1f} '
            f'H{x + 8 * s:.1f} V{y + 5.5 * s:.1f}" fill="none" stroke="{color}" stroke-width="{1.3 * s}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def zipper(x0, x1, cy) -> str:
    """A chrome zip running along the section rule — the hardware of latex."""
    o = [f'<rect x="{x0}" y="{cy - 6}" width="{x1 - x0}" height="12" fill="#0b0b0b"/>',
         f'<rect x="{x0}" y="{cy - 6}" width="{x1 - x0}" height="1" fill="#fff" fill-opacity=".07"/>',
         f'<rect x="{x0}" y="{cy + 5}" width="{x1 - x0}" height="1.5" fill="#000" fill-opacity=".6"/>']
    x, i = x0 + 22, 0
    while x < x1 - 14:
        y = cy - 5.6 if i % 2 == 0 else cy - 0.2
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="2.6" height="5.6" rx=".6" fill="url(#chrome)"/>')
        x += 4.6
        i += 1
    # slider + pull tab
    o.append(f'<rect x="{x0 + 3}" y="{cy - 9}" width="13" height="18" rx="3" fill="url(#ring)" stroke="#111" stroke-width=".6"/>')
    o.append(f'<rect x="{x0 + 6.5}" y="{cy + 7}" width="6" height="13" rx="1.8" fill="url(#chrome)" stroke="#111" stroke-width=".5"/>')
    o.append(f'<circle cx="{x0 + 9.5}" cy="{cy + 15.5}" r="1.3" fill="#111"/>')
    # end stop
    o.append(f'<rect x="{x1 - 5}" y="{cy - 6}" width="5" height="12" rx="1" fill="url(#ring)"/>')
    return "".join(o)


# ── plates ──────────────────────────────────────────────────────────────────
def hero() -> str:
    h = 380
    b = [plate(h), f'<rect width="{W}" height="{h}" fill="url(#lamp)"/>']
    creases = [
        ("M-20 300 C 150 258, 330 342, 540 280 S 820 244, 930 276", .15, 1.6),
        ("M-20 86 C 150 132, 340 54, 520 110 S 780 162, 930 120", .09, 1.2),
        ("M-20 352 C 240 330, 470 368, 700 340 S 880 324, 930 332", .11, 1.3),
    ]
    for d, op, w in creases:  # each fold: a soft shadow, then the wet highlight along the ridge
        b.append(f'<path d="{d}" transform="translate(0 3)" fill="none" stroke="#000" stroke-opacity=".5" '
                 f'stroke-width="{w + 3}" filter="url(#soft2)"/>')
        b.append(f'<path d="{d}" fill="none" stroke="url(#fade)" stroke-opacity="{op}" stroke-width="{w}" filter="url(#soft)"/>')
    b.append(band(300, 240, h, "sheen", .9))
    b.append(band(322, 26, h, "sheenS", .8))
    # the slow light sweep
    b.append(f'<g><rect x="0" y="-80" width="170" height="{h + 160}" fill="url(#sweep)" transform="skewX(-22)"/>'
             f'<animateTransform attributeName="transform" type="translate" values="-420 0;1380 0;1380 0" '
             f'keyTimes="0;0.42;1" dur="12s" calcMode="spline" keySplines="0.45 0 0.25 1;0 0 1 1" repeatCount="indefinite"/></g>')
    b.append(f'<rect width="{W}" height="{h}" fill="url(#vig)"/>')

    # masthead
    handle, est = "L0stInFades", "EST. MMXXIV"
    b.append('<circle cx="48" cy="36.5" r="3" fill="url(#red)"/>')
    b.append(T(58, 40, handle, "label", 11, SOFT, tracking=3.4))
    b.append(T(852, 40, est, "label", 11, DIM, anchor="end", tracking=3.4))
    hw = F["label"].width(handle, 11, 3.4)
    ew = F["label"].width(est, 11, 3.4)
    b.append(f'<line x1="{58 + hw + 18:.0f}" y1="36.5" x2="{852 - ew - 18:.0f}" y2="36.5" stroke="{HAIR}"/>')

    # the name — glossy crimson latex
    name = "Raaaaaymond"
    size = fit("name", name, 740, 128)
    y = 214
    b.append(T(450, y + 7, name, "name", size, "#000", anchor="middle", extra='opacity=".7" filter="url(#soft4)"'))
    b.append(T(450, y, name, "name", size, "url(#red)", anchor="middle", extra='filter="url(#rubberH)"'))
    b.append(T(450, y, name, "name", size, "url(#spec)", anchor="middle"))

    # role line
    role = "SYSTEMS · ENGINES · PROOFS · MUSIC"
    rw = F["label"].width(role, 10.5, 5)
    ry = 262
    b.append(T(450, ry, role, "label", 10.5, SOFT, anchor="middle", tracking=5))
    b.append(f'<line x1="150" y1="{ry - 4}" x2="{450 - rw / 2 - 22:.0f}" y2="{ry - 4}" stroke="url(#ruleL)"/>'
             f'<line x1="{450 + rw / 2 + 22:.0f}" y1="{ry - 4}" x2="750" y2="{ry - 4}" stroke="url(#ruleR)"/>')

    # tagline — crossfading lines
    lines = ["systems that think — music that computes", "proofs where words fall silent",
             "engines for worlds not yet rendered", "compression as meditation",
             "writing compilers for the unnameable"]
    per = 4.2
    dur = per * len(lines)
    for i, l in enumerate(lines):
        use("ital", l)
        kt = f"0;{0.9 / dur:.4f};{(per - 0.9) / dur:.4f};{per / dur:.4f};1"
        b.append(f'<text x="450" y="318" font-family="{F["ital"].family}" font-size="21" fill="{SOFT}" '
                 f'text-anchor="middle" opacity="0">{esc(l)}'
                 f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="{kt}" dur="{dur}s" '
                 f'begin="{i * per}s" repeatCount="indefinite"/></text>')
    defs = rubber("rubberH", 240, -420, 620, blur=2.4, scale=6, k=.85, exp=24)
    return svg(h, "".join(b), ["label", "name", "ital"], defs, "Raaaaaymond — L0stInFades")


def statement() -> str:
    h = 132
    b = [plate(h), band(560, 180, h, "sheen", .6), band(578, 16, h, "sheenS", .35)]
    b.append('<rect x="436" y="18" width="28" height="2.5" rx="1.25" fill="url(#red)"/>')
    lines = ["I work at the edges of computing —",
             "building game engines, verifying mathematics, composing algorithms into music.",
             "Each project is an attempt to find the precise language a problem deserves."]
    for i, l in enumerate(lines):
        b.append(T(450, 54 + i * 28, l, "ital", 18.5, SOFT, anchor="middle"))
    b.append(seam(h))
    return svg(h, "".join(b), ["ital"], "", " ".join(lines))


def section(n: int, label: str) -> str:
    h = 80
    b = [plate(h), band(560 + n * 60, 140, h, "sheen", .45)]
    num = f"0{n}"
    nx, ny = 48, 53
    b.append(T(nx, ny, num, "italb", 26, "url(#red)"))
    b.append(T(nx, ny, num, "italb", 26, "url(#spec)"))
    nw = F["italb"].width(num, 26)
    lx = nx + nw + 16
    b.append(T(lx, 49, label, "label", 12, "#e8e8e8", tracking=4.6))
    lw = F["label"].width(label, 12, 4.6)
    b.append(zipper(lx + lw + 26, 852, 44))
    return svg(h, "".join(b), ["italb", "label"], "", f"{num} — {label.title()}")


def currently() -> str:
    h = 176
    b = [plate(h), band(600, 220, h, "sheen", .7), band(622, 20, h, "sheenS", .55)]
    title, ts = "edyt.video", 40
    b.append(T(48, 66, title, "italb", ts, "url(#red)", extra='filter="url(#rubberS)"'))
    b.append(T(48, 66, title, "italb", ts, "url(#spec)"))
    tw = F["italb"].width(title, ts)
    b.append(T(48 + tw + 22, 64, "MOTION DESIGN VIDEO EDITOR", "label", 10.5, SOFT, tracking=3.6))
    b.append(T(48, 100, "clean, ready-to-ship animations without the usual complexity.", "body", 15, TXT))
    b.append(T(48, 126, "smooth curve-based pathing · shape morphing · camera system · stagger reveals", "body", 14, DIM))
    pt = "EARLY ACCESS"
    pw = F["label"].width(pt, 10, 3) + 30
    b.append(f'<rect x="{852 - pw:.1f}" y="40" width="{pw:.1f}" height="24" rx="12" fill="{CR}" fill-opacity=".07" '
             f'stroke="url(#red)" stroke-width="1.1"/>')
    b.append(T(852 - pw / 2, 56, pt, "label", 10, CR, anchor="middle", tracking=3))
    b.append(T(852 - 16, 126, "OPEN", "label", 10, DIM, anchor="end", tracking=3))
    b.append(arrow(852 - 9, 117, DIM))
    b.append(seam(h))
    defs = rubber("rubberS", 40, -160, 240, blur=1.2, scale=3, k=.7, exp=20)
    return svg(h, "".join(b), ["italb", "label", "body"], defs,
               "edyt.video — motion design video editor · early access")


PROJECTS = [
    ("Afterglow", "iOS Photos-style image viewer for Windows · Direct2D + DirectComposition · spring physics · hero transitions",
     "C++ · DIRECT2D", "https://github.com/L0stInFades/Afterglow"),
    ("ember", "from-scratch RISC-V cores, single-cycle to out-of-order · an RV32IMAC/Sv32 MMU SoC that boots Linux to a shell",
     "VERILOG · RISC-V", "https://github.com/L0stInFades/ember"),
    ("BlameEngine", "headless authoritative-world game engine · UE5 view client + Jolt physics · a real-code hacking sandbox",
     "C++ · UE5 · JOLT", "https://github.com/L0stInFades/BlameEngine"),
    ("AnalysisTrinity", "formal proofs of Nested Intervals · Bolzano–Weierstrass · Heine–Borel — the completeness trinity",
     "LEAN 4", "https://github.com/L0stInFades/AnalysisTrinity"),
    ("nocturnes-in-code", "algorithmic compositions — neoclassical fugues, IDM drum machines, melodic techno, synthesized from scratch",
     "SUPERCOLLIDER", "https://github.com/L0stInFades/nocturnes-in-code"),
    ("Nevermind-Lang", "a language.",
     "RUST", "https://github.com/L0stInFades/Nevermind-Lang"),
    ("Quench", "compression as meditation · extraction as gentle unfolding",
     "RUST", "https://github.com/L0stInFades/Quench"),
    ("Cocode-Precise", "MCP server for exact code symbol retrieval — whole functions and classes, nothing more",
     "PYTHON · MCP", "https://github.com/L0stInFades/Cocode-Precise"),
]


def work(i: int, name: str, desc: str, tag: str) -> str:
    h = 96
    b = [plate(h), band(120 + (i * 197) % 640, 110, h, "sheen", .55)]
    b.append(T(48, 44, f"0{i + 1}", "italb", 15, "url(#red)"))
    b.append(T(96, 44, name, "title", 27, "url(#silver)"))
    ds = fit("body", desc, 740, 13.5)
    b.append(T(96, 69, desc, "body", ds, DIM))
    b.append(T(852, 42, tag, "mono", 10.5, CR, anchor="end", tracking=1.4))
    b.append(arrow(852 - 8, 58, FAINT))
    b.append(seam(h))
    return svg(h, "".join(b), ["italb", "title", "body", "mono"], "", f"{name} — {desc}")


STACK = ["C++", "RUST", "TYPESCRIPT", "PYTHON", "OCAML", "LEAN 4",
         "VERILOG", "GLEAM", "SUPERCOLLIDER", "ELECTRON", "LINUX", "VIM"]


def stack() -> str:
    h = 128
    b = [plate(h), band(700, 160, h, "sheen", .5)]
    rows = [STACK[:6], STACK[6:]]
    for r, row in enumerate(rows):
        cy = 40 + r * 46
        ws = [F["label"].width(t, 11, 2.6) + 34 for t in row]
        gap = 12
        x = 450 - (sum(ws) + gap * (len(row) - 1)) / 2
        for t, w in zip(row, ws):
            b.append(f'<rect x="{x:.1f}" y="{cy - 15}" width="{w:.1f}" height="30" rx="15" fill="url(#pill)" '
                     f'stroke="url(#ring)" stroke-width="1" stroke-opacity=".85"/>')
            b.append(f'<rect x="{x + 10:.1f}" y="{cy - 14}" width="{w - 20:.1f}" height="1" rx=".5" fill="#fff" fill-opacity=".12"/>')
            b.append(T(x + w / 2, cy + 4, t, "label", 11, "#dcdcdc", anchor="middle", tracking=2.6))
            x += w + gap
    b.append(seam(h))
    return svg(h, "".join(b), ["label"], "", "Stack: " + ", ".join(STACK))


def footer() -> str:
    h = 124
    b = [plate(h), band(200, 200, h, "sheen", .5)]
    y, x0, x1 = 44, 48, 852
    b.append(f'<rect x="{x0}" y="{y + 5}" width="{x1 - x0}" height="26" rx="13" fill="#000" opacity=".6" filter="url(#soft4)"/>')
    b.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="26" rx="13" fill="url(#strap)"/>')
    b.append(f'<rect x="{x0 + 12}" y="{y + 2}" width="{x1 - x0 - 24}" height="1.2" rx=".6" fill="#fff" fill-opacity=".28" filter="url(#soft)"/>')
    b.append(f'<rect x="{x0 + 12}" y="{y + 22.5}" width="{x1 - x0 - 24}" height="1" fill="#000" fill-opacity=".7"/>')
    for gx in (110, 210, 310, 590, 690, 790):  # grommets
        b.append(f'<circle cx="{gx}" cy="{y + 13}" r="5.2" fill="{INK}" stroke="url(#ring)" stroke-width="2.4"/>')
    bx = 450  # buckle
    b.append(f'<rect x="{bx - 22}" y="{y - 8}" width="44" height="42" rx="7" fill="none" stroke="#000" stroke-opacity=".7" '
             f'stroke-width="7" filter="url(#soft2)" transform="translate(0 3)"/>')
    b.append(f'<rect x="{bx - 22}" y="{y - 8}" width="44" height="42" rx="7" fill="none" stroke="url(#ring)" stroke-width="5"/>')
    b.append(f'<path d="M{bx - 19} {y + 13} H{bx + 16}" stroke="url(#chrome)" stroke-width="3.2" stroke-linecap="round"/>')
    b.append(T(450, 104, "L0STINFADES · MMXXVI", "label", 9.5, DIM, anchor="middle", tracking=4.5))
    return svg(h, "".join(b), ["label"], "", "L0stInFades · 2026")


def colophon() -> str:
    """495×195 — sits beside the streak card (same aspect ratio) as a lookbook credit box."""
    w, h = 495, 195
    b = [plate(h, w), band(330, 120, h, "sheen", .6), band(346, 12, h, "sheenS", .35)]
    rows = [("MATERIAL", "black latex · crimson · chrome"),
            ("TYPE", "Bodoni Moda · Montserrat"),
            ("", "Inter · JetBrains Mono"),
            ("HARDWARE", "zips · O-rings · one buckle"),
            ("CUT & SEWN", "assets/latex/gen.py")]
    b.append(T(36, 40, "COLOPHON", "label", 9.5, CR, tracking=3.6))
    b.append(f'<line x1="36" y1="49" x2="{36 + F["label"].width("COLOPHON", 9.5, 3.6):.0f}" y2="49" stroke="url(#red)" stroke-width="1"/>')
    for i, (k, v) in enumerate(rows):
        y = 74 + i * 24
        if k:
            b.append(T(36, y, k, "label", 8.5, DIM, tracking=2.4))
        b.append(T(128, y, v, "body", 12, TXT))
    # a chrome O-ring — the one piece of hardware given the whole frame
    cx, cy = 436, 104
    b.append(f'<circle cx="{cx}" cy="{cy + 4}" r="27" fill="none" stroke="#000" stroke-opacity=".7" stroke-width="11" filter="url(#soft4)"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="27" fill="none" stroke="url(#ring)" stroke-width="8.5"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="31.3" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width=".8"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="22.7" fill="none" stroke="#000" stroke-opacity=".5" stroke-width=".8"/>')
    b.append(seam(h, w))
    return svg(h, "".join(b), ["label", "body"], "", "Colophon — black latex, crimson, chrome · Bodoni Moda, Montserrat, Inter, JetBrains Mono", w)


# ── README ──────────────────────────────────────────────────────────────────
def img(src, alt, width="100%"):
    return f'<img src="{src}" alt="{esc(alt)}" align="top" width="{width}">'


def link(href, inner):
    return f'<a href="{href}">{inner}</a>'


STATS = ("https://github-readme-stats-sigma-five.vercel.app/api?username=L0stInFades&show_icons=true&hide_border=true"
         "&card_width=495&bg_color=050505&title_color=ff2d55&text_color=8a8a8a&icon_color=ff2d55&ring_color=ff2d55")
STREAK = ("https://streak-stats.demolab.com?user=L0stInFades&hide_border=true&background=050505&ring=ff2d55&fire=ff2d55"
          "&currStreakNum=e6e6e6&sideNums=e6e6e6&currStreakLabel=ff2d55&sideLabels=8a8a8a&dates=5a5a5a&stroke=1f1f1f")
SNAKE = "https://raw.githubusercontent.com/L0stInFades/L0stInFades/output/snake-latex.svg"
CONTRIB3D = "profile-3d-contrib/profile-latex.svg"


def readme(rows):
    A = ASSET_PREFIX
    out = ['<!-- generated by assets/latex/gen.py — edit that, not this -->', '<div align="center">']
    out.append(link(PROFILE_URL, img(A + "hero.svg", "Raaaaaymond — L0stInFades")))
    out.append(link(PROFILE_URL, img(A + "statement.svg", "I work at the edges of computing — building game engines, verifying mathematics, composing algorithms into music. Each project is an attempt to find the precise language a problem deserves.")))
    out.append(link("https://edyt.video", img(A + "sec-01-currently.svg", "01 — Currently")))
    out.append(link("https://edyt.video", img(A + "now-edyt.svg", "edyt.video — motion design video editor · early access")))
    out.append(link(PROFILE_URL + "?tab=repositories", img(A + "sec-02-work.svg", "02 — Selected work")))
    for (name, desc, tag, url), fname in rows:
        out.append(link(url, img(A + fname, f"{name} — {desc}")))
    out.append(link(PROFILE_URL, img(A + "sec-03-stack.svg", "03 — Stack")))
    out.append(link(PROFILE_URL, img(A + "stack.svg", "Stack: " + ", ".join(STACK))))
    out.append(link(PROFILE_URL, img(A + "sec-04-activity.svg", "04 — Activity")))
    # The external cards (STATS / STREAK above) are deliberately not used: the self-hosted
    # stats instance answers with an error card until PAT_1 is set on Vercel, and
    # streak-stats.demolab.com keeps failing behind GitHub's image proxy. ledger.svg
    # (assets/latex/ledger.py, refreshed daily by the 3d-contrib workflow) replaces them.
    out.append(link(PROFILE_URL, img(A + "ledger.svg", "Contributions and streaks", "50%"))
               + link(PROFILE_URL, img(A + "colophon.svg", "Colophon", "50%")))
    out.append(link(PROFILE_URL, img(CONTRIB3D, "3D contribution graph")))
    out.append(link(PROFILE_URL, img(SNAKE, "contribution snake")))
    out.append(link(PROFILE_URL, img(A + "footer.svg", "L0stInFades · 2026")))
    out.append('</div>')
    return "\n".join(out) + "\n"


def main():
    files = {
        "hero.svg": hero(),
        "statement.svg": statement(),
        "sec-01-currently.svg": section(1, "CURRENTLY"),
        "now-edyt.svg": currently(),
        "sec-02-work.svg": section(2, "SELECTED WORK"),
        "sec-03-stack.svg": section(3, "STACK"),
        "stack.svg": stack(),
        "sec-04-activity.svg": section(4, "ACTIVITY"),
        "footer.svg": footer(),
        "colophon.svg": colophon(),
    }
    rows = []
    for i, p in enumerate(PROJECTS):
        fname = f"work-{i + 1:02d}-{p[0].lower()}.svg"
        files[fname] = work(i, p[0], p[1], p[2])
        rows.append((p, fname))
    total = 0
    for fname, content in files.items():
        path = os.path.join(HERE, fname)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        total += len(content.encode())
        print(f"  {fname:28s} {len(content.encode()) / 1024:6.1f} KB")
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(readme(rows))
    print(f"  README.md  ->  {README}\n  total assets: {total / 1024:.0f} KB")


if __name__ == "__main__":
    main()
