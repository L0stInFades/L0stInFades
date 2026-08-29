#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger.py — sets assets/readme/ledger.svg: total contributions and streaks, on the page.

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
from gen import HAIR, HAIR2, INK, MUTED, T, caps, paper, svg, vline  # noqa: E402

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
                     "User-Agent": "readme-ledger"})
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
    days: dict = {}
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
        return f"{a.day} {a:%B}"
    if a.year != b.year:
        return f"{a.day} {a:%B %Y} – {b.day} {b:%B %Y}"
    if a.month == b.month:
        return f"{a.day}–{b.day} {b:%B}"
    return f"{a.day} {a:%B} – {b.day} {b:%B}"


def render(total: int, current, best, created, today) -> str:
    w, h = gen.W, 180
    b = [paper(h)]
    cols = [(270, f"{total:,}", "contributions in all", f"since {created:%B}, {created:%Y}"),
            (450, f"{current[0]:,}", "the present streak", span(current[1], current[2])),
            (630, f"{best[0]:,}", "the longest streak", span(best[1], best[2]))]
    for x, num, label, sub in cols:
        b.append(T(x, 84, num, "display", 54, INK, anchor="middle",
                   extra='style="font-feature-settings:&quot;lnum&quot; 1"'))
        b.append(caps(x, 112, label, 10, MUTED, "middle", .26))
        b.append(T(x, 134, sub, "texti", 13.5, MUTED, anchor="middle"))
    for x in (360, 540):
        b.append(vline(x, 52, 144, HAIR))
    b.append(caps(450, 164, f"reckoned on {today.day} {today:%B %Y}", 9, HAIR2, "middle", .26))
    title = (f"{total} contributions since {created:%B %Y} · the present streak {current[0]} days · "
             f"the longest streak {best[0]} days")
    return svg(h, "".join(b), ["display", "caps", "texti"], "", title, w)


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
