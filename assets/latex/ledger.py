#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger.py — renders assets/latex/ledger.svg: total contributions and streaks, in the
house style (a 495×195 plate that sits beside colophon.svg).

Run daily by .github/workflows/3d-contrib.yml with GITHUB_TOKEN; locally it falls back
to `gh api graphql`. Needs:  pip install fonttools brotli
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen  # noqa: E402
from gen import CR, DIM, FAINT, SOFT, F, T, band, plate, seam, svg  # noqa: E402

LOGIN = "L0stInFades"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.svg")

QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){ createdAt
    contributionsCollection(from:$from,to:$to){
      contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }"""


def gql(variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": variables}).encode(),
            headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                     "User-Agent": "latex-ledger"})
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
    else:  # local: borrow the gh CLI's login
        args = ["gh", "api", "graphql", "-f", f"query={QUERY}"]
        for k, v in variables.items():
            args += ["-f", f"{k}={v}"]
        payload = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)
    if "errors" in payload:
        raise SystemExit(payload["errors"])
    return payload["data"]


def fetch():
    """Every day since the account was created -> {date: count}."""
    now = dt.datetime.now(dt.timezone.utc)
    probe = gql({"login": LOGIN, "from": (now - dt.timedelta(days=7)).isoformat(), "to": now.isoformat()})
    created = dt.datetime.fromisoformat(probe["user"]["createdAt"].replace("Z", "+00:00"))
    days: dict[str, int] = {}
    start = created.replace(hour=0, minute=0, second=0, microsecond=0)
    while start < now:
        end = min(start + dt.timedelta(days=365), now)
        cal = gql({"login": LOGIN, "from": start.isoformat(), "to": end.isoformat()})
        for week in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
        start = end
    return days, created


def streaks(days: dict):
    today = dt.datetime.now(dt.timezone.utc).date()
    best, run, run_start, prev = (0, None, None), 0, None, None
    for ds in sorted(days):
        d = dt.date.fromisoformat(ds)
        if days[ds] > 0:
            if run and prev is not None and (d - prev).days == 1:
                run += 1
            else:
                run, run_start = 1, d
            if run > best[0]:
                best = (run, run_start, d)
        else:
            run = 0
        prev = d
    d = today if days.get(today.isoformat(), 0) else today - dt.timedelta(days=1)  # today may still be empty
    cur_end, cur = d, 0
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    current = (cur, d + dt.timedelta(days=1), cur_end) if cur else (0, None, None)
    return current, best


def span(a, b) -> str:
    if not a:
        return "—"
    if a == b:
        return f"{a:%b %d}"
    return f"{a:%b %d} – {b:%b %d}" if a.year == b.year else f"{a:%b %d %Y} – {b:%b %d %Y}"


def render(total: int, current, best, created, today) -> str:
    w, h = 495, 195
    b = [plate(h, w), band(150, 90, h, "sheen", .5), band(164, 12, h, "sheenS", .3)]
    b.append(T(36, 40, "LEDGER", "label", 9.5, CR, tracking=3.6))
    b.append(f'<line x1="36" y1="49" x2="{36 + F["label"].width("LEDGER", 9.5, 3.6):.0f}" y2="49" '
             f'stroke="url(#red)" stroke-width="1"/>')
    b.append(T(459, 40, f"AS OF {today:%d %b %Y}".upper(), "label", 8, FAINT, anchor="end", tracking=2))
    cols = [(82, f"{total:,}", "CONTRIBUTIONS", f"since {created:%b %Y}"),
            (247, f"{current[0]:,}", "CURRENT STREAK", span(current[1], current[2])),
            (412, f"{best[0]:,}", "LONGEST STREAK", span(best[1], best[2]))]
    for x, num, label, sub in cols:
        size = gen.fit("name", num, 130, 46)
        b.append(T(x, 100, num, "name", size, "url(#red)", anchor="middle", extra='filter="url(#rubberL)"'))
        b.append(T(x, 100, num, "name", size, "url(#spec)", anchor="middle"))
        b.append(T(x, 127, label, "label", 8.5, SOFT, anchor="middle", tracking=2.6))
        b.append(T(x, 146, sub, "body", 10.5, DIM, anchor="middle"))
    for x in (165, 330):
        b.append(f'<line x1="{x}" y1="58" x2="{x}" y2="158" stroke="url(#ruleV)"/>')
    b.append(seam(h, w))
    defs = ('<filter id="rubberL" x="-10%" y="-25%" width="120%" height="150%">'
            '<feGaussianBlur in="SourceAlpha" stdDeviation="1.3" result="b"/>'
            '<feSpecularLighting in="b" surfaceScale="3.5" specularConstant=".75" specularExponent="20" '
            'lighting-color="#fff" result="s"><feDistantLight azimuth="235" elevation="55"/></feSpecularLighting>'
            '<feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/>'
            '<feComposite in="SourceGraphic" in2="s2" operator="arithmetic" k1="0" k2="1" k3="1" k4="0"/></filter>'
            '<linearGradient id="ruleV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#151515"/>'
            '<stop offset=".5" stop-color="#4a4a4a"/><stop offset="1" stop-color="#151515"/></linearGradient>')
    title = (f"{total} contributions since {created:%B %Y} · current streak {current[0]} days · "
             f"longest streak {best[0]} days")
    return svg(h, "".join(b), ["label", "name", "body"], defs, title, w)


def main():
    days, created = fetch()
    current, best = streaks(days)
    total = sum(days.values())
    today = dt.datetime.now(dt.timezone.utc).date()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(total, current, best, created, today))
    print(f"  ledger.svg  total={total}  current={current[0]}  longest={best[0]}  "
          f"({os.path.getsize(OUT) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
