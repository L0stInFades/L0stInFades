#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger.py — sets assets/readme/ledger-light.svg and ledger-dark.svg: total contributions
and streaks, in the manner of the rest of the page (the plate itself is gen.ledger).

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

LOGIN = gen.HANDLE
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger-{theme}.svg")

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


def span(a, b, month="%B") -> str:
    if not a:
        return "—"
    if a == b:
        return f"{a.day} {a:{month}}"
    if a.year != b.year:
        return f"{a.day} {a:{month} %Y} – {b.day} {b:{month} %Y}"
    if a.month == b.month:
        return f"{a.day}–{b.day} {b:{month}}"
    return f"{a.day} {a:{month}} – {b.day} {b:{month}}"


def spans(a, b):
    """The same span of days in full and with the months cut short, for a narrow column."""
    return [span(a, b), span(a, b, "%b")]


def figures(total: int, current, best, created):
    return [(f"{total:,}", "contributions in all", [f"since {created:%B}, {created:%Y}", f"since {created:%b} {created:%Y}"]),
            (f"{current[0]:,}", "the present streak", spans(current[1], current[2])),
            (f"{best[0]:,}", "the longest streak", spans(best[1], best[2]))]


def main():
    days, created = fetch()
    current, best = streaks(days)
    total = sum(days.values())
    today = dt.datetime.now(dt.timezone.utc).date()
    note = f"reckoned on {today.day} {today:%B %Y}"
    for t in gen.THEMES:
        out = OUT.format(theme=t.key)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(gen.ledger(t, figures(total, current, best, created), note))
        print(f"  {os.path.basename(out)}  total={total}  current={current[0]}  longest={best[0]}  "
              f"({os.path.getsize(out) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
