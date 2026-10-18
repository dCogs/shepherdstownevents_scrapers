#!/usr/bin/env python3
"""
Build an .ics calendar from a FareHarbor item's availabilities.

FareHarbor's calendar page is an empty JS shell; the month grid is filled
from a JSON endpoint that already contains every time slot for the month,
so no per-date clicking is needed:

  https://fareharbor.com/api/v1/companies/<company>/items/<item>/calendar/<YYYY>/<MM>/

Usage:
  python3 fareharbor_ics.py                          # this month + next 2
  python3 fareharbor_ics.py --months 6 -o walks.ics
  python3 fareharbor_ics.py --start 2026-10 --months 3 --dump raw/
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timedelta
from datetime import date

import requests

COMPANY = "shepherdstownmysterywalks"
ITEM = 190345
API = "https://fareharbor.com/api/v1/companies/{c}/items/{i}/calendar/{y}/{m:02d}/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://fareharbor.com/embeds/book/{c}/items/{i}/calendar/",
}


def months(start: dt.date, n: int):
    y, m = start.year, start.month
    for _ in range(n):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch_month(session, company, item, y, m):
    url = API.format(c=company, i=item, y=y, m=m)
    r = session.get(url, params={"allow_grouped": "yes", "bookable_only": "no"},
                    timeout=30)
    r.raise_for_status()
    return r.json()


def find_availabilities(obj):
    """Walk the JSON and yield every dict that looks like an availability
    (has start_at). Robust to FareHarbor reshuffling the nesting
    (calendar -> weeks -> days -> availabilities)."""
    if isinstance(obj, dict):
        if "start_at" in obj and ("pk" in obj or "end_at" in obj):
            yield obj
            return
        for v in obj.values():
            yield from find_availabilities(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_availabilities(v)


def parse_ts(s):
    # FareHarbor uses e.g. "2026-10-24T19:00:00-0400"
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return dt.datetime.fromisoformat(s)


def ics_escape(s):
    return (str(s).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def utc(d):
    return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# Fixed fields, matching ghost.ics
UID_SUFFIX = "85b455c0-974a-5d17-afe0-f60a7c4154af@ghost"
SUMMARY = "Ghost Tour / History Tour"
LOCATION = "Welcome Center at the Market House, 100 East German St, Shepherdstown"
DESCRIPTION = (
    "Stroll through historic Shepherdstown on a 90\u2011minute candlelit walk led by a "
    "costumed guide who shares ghost stories, local mystery, and town history from "
    "early settlers through the Civil War and the building of the C&O Canal. The tour "
    "blends spooky tales of lingering residents with scenic views along the Potomac "
    "River and the charm of West Virginia\u2019s oldest town. Enjoy atmospheric "
    "storytelling that highlights Hollywood connections, regional lore, and the "
    "unique character of this quaint riverside community."
)
SITE = "https://shepherdstownmysterywalks.com/"
IMAGE_URL = "shepherdstownmysterywalks.com/wp-content/uploads/2023/04/download-_5_.jpg"


def to_event(a, dtstamp):
    start = parse_ts(a["start_at"])
    end = parse_ts(a["end_at"]) if a.get("end_at") else start + dt.timedelta(minutes=90)
    return [
        "BEGIN:VEVENT",
        f"UID:{utc(start)}-{UID_SUFFIX}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{utc(start)}",
        f"DTEND:",
        f"SUMMARY:{SUMMARY}",
        f"LOCATION:{LOCATION}",
        f"DESCRIPTION:{ics_escape(DESCRIPTION)}",
        "CATEGORIES:History",
        "ORGANIZATION:Shepherdstown Mystery Walks",
        f"URL:{SITE}",
        "STATUS:CONFIRMED",
        "SOURCE:shepherdstownmysterywalks.com/",
        f"IMAGE_URL:{IMAGE_URL}",
        "SEQUENCE:0",
        "END:VEVENT",
    ], start


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--company", default=COMPANY)
    p.add_argument("--item", type=int, default=ITEM)
    p.add_argument("--start", help="YYYY-MM (default: current month)")
    p.add_argument("--months", type=int, default=3)
    p.add_argument("-o", "--output", default="shepherdstown_mystery_walks.ics")
    p.add_argument("--dump", help="directory to save raw month JSON (debugging)")
    args = p.parse_args()

    today = datetime.today()
    today_formatted = today.strftime("%Y%m%d")
    output_file = 'ghost_' + today_formatted + '.ics'

    start = (dt.datetime.strptime(args.start, "%Y-%m").date() if args.start
             else dt.date.today().replace(day=1))

    s = requests.Session()
    s.headers.update({k: v.format(c=args.company, i=args.item)
                      for k, v in HEADERS.items()})

    dtstamp = utc(dt.datetime.now(dt.timezone.utc))
    seen, events = set(), []
    for y, m in months(start, args.months):
        try:
            data = fetch_month(s, args.company, args.item, y, m)
        except requests.HTTPError as e:
            print(f"{y}-{m:02d}: HTTP {e.response.status_code}", file=sys.stderr)
            continue
        if args.dump:
            d = pathlib.Path(args.dump)
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{y}-{m:02d}.json").write_text(json.dumps(data, indent=2))
        n = 0
        for a in find_availabilities(data):
            key = utc(parse_ts(a["start_at"]))  # one event per start time
            if key in seen:  # calendar weeks overlap month boundaries
                continue
            if a.get("is_cancelled") or a.get("status") == "cancelled":
                continue
            seen.add(key)
            events.append(to_event(a, dtstamp))
            n += 1
        print(f"{y}-{m:02d}: {n} slots", file=sys.stderr)

    events.sort(key=lambda e: e[1])
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//potomacaudubon.org//calendar//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:Shepherdstown Mystery Walks Calendar",
             "X-WR-TIMEZONE:America/New_York"]
    for ev, _ in events:
        lines += ev
    lines.append("END:VCALENDAR")
    pathlib.Path(output_file).write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(events)} events to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()