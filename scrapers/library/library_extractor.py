#!/usr/bin/env python3
"""
Shepherdstown Public Library events -> .ics

The site runs The Events Calendar (WordPress). Its REST API
(/wp-json/tribe/events/v1/) is blocked, so this tries, in order:

  1. The plugin's own iCal export (?ical=1)  -- if enabled, used as-is for times
  2. The schema.org JSON-LD <script> blocks the plugin embeds in every
     list page (/events/list/, /events/list/page/2/, ...)

Usage:
  python3 sheplibrary_ics.py                    # up to 5 list pages
  python3 sheplibrary_ics.py --pages 10 -o sheplibrary.ics
  python3 sheplibrary_ics.py --source jsonld    # skip the iCal attempt
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys

import requests

from datetime import datetime, timedelta
from datetime import date

BASE = "https://www.sheplibrary.org"
LIST = BASE + "/events/list/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
}
ORG = "Shepherdstown Public Library"
DEFAULT_LOCATION = "Shepherdstown Public Library, 145 S Princess St, Shepherdstown"
CATEGORY = "Library"


# ---------- helpers ----------
def utc(d):
    # return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return d.strftime("%Y%m%dT%H%M%S")



def local_z(d):
    """Eastern clock time written with a Z
    (a 7pm event -> T190000Z) and what the importer expects."""
    return eastern_now(d).strftime("%Y%m%dT%H%M%S")


def esc(s):
    return (str(s).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\r", "").replace("\n", "\\n"))


def strip_html(s):
    s = html.unescape(s or "")  # TEC entity-encodes the HTML inside JSON-LD
    s = re.sub(r"<br\s*/?>|</p>", "\n", s or "", flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


EASTERN = None


def eastern(naive_or_aware):
    """The library's feed labels Eastern clock times as UTC, so drop whatever
    offset the source claims and attach America/New_York."""
    global EASTERN
    if EASTERN is None:
        from zoneinfo import ZoneInfo
        EASTERN = ZoneInfo("America/New_York")
    return naive_or_aware.replace(tzinfo=EASTERN)


def eastern_now(d):
    eastern(d.replace(tzinfo=None))  # ensure EASTERN loaded
    return d.astimezone(EASTERN)


def parse_iso(s):
    return eastern(dt.datetime.fromisoformat(s.replace("Z", "+00:00")))


def location_str(loc):
    if isinstance(loc, list):
        loc = loc[0] if loc else None
    if not isinstance(loc, dict):
        return DEFAULT_LOCATION
    name = loc.get("name", "")
    a = loc.get("address") or {}
    if isinstance(a, dict):
        parts = [a.get("streetAddress"), a.get("addressLocality")]
    else:
        parts = [str(a)]
    s = ", ".join(p for p in [name, *parts] if p)
    return html.unescape(s) or DEFAULT_LOCATION


# ---------- source 1: plugin's iCal export ----------
def fetch_ical(session, start_date=None):
    """One iCal request. The plugin caps each export at ~30 events, so
    callers page forward with tribe-bar-date (list view's start date)."""
    for url in (LIST, BASE + "/"):
        params = {"ical": "1"}
        if url == BASE + "/":
            params.update(post_type="tribe_events", eventDisplay="list")
        if start_date:
            params["tribe-bar-date"] = start_date.isoformat()
        try:
            r = session.get(url, params=params, timeout=30)
        except requests.RequestException:
            continue
        if r.ok and r.text.lstrip().startswith("BEGIN:VCALENDAR"):
            return r.text
    return None


def ical_all(session, until, max_requests=24):
    """Page through the capped iCal export until `until` or no new events."""
    events, seen, cursor = [], set(), None
    for _ in range(max_requests):
        text = fetch_ical(session, cursor)
        if text is None:
            break
        new = 0
        for e in events_from_ical(text):
            key = (e["name"], e["start"])
            if e["start"] is None or key in seen:
                continue
            seen.add(key)
            events.append(e)
            new += 1
        print(f"iCal from {cursor or 'today'}: {new} new events", file=sys.stderr)
        if not new:
            break
        last = max(e["start"] for e in events).date()
        if last >= until or last == cursor:
            break
        # restart on the last day seen (not the day after) so events later
        # that same day aren't skipped; duplicates are filtered above
        cursor = last
    return [e for e in events if e["start"].date() <= until]


def events_from_ical(text):
    """Minimal unfold+parse; keeps what we need for our own output format."""
    from zoneinfo import ZoneInfo
    text = re.sub(r"\r?\n[ \t]", "", text)
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        f = {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            name, *params = k.split(";")
            f[name] = (v, params)

        def when(key):
            if key not in f:
                return None
            v, params = f[key]
            v = v.rstrip("Z")
            fmt = "%Y%m%d" if "VALUE=DATE" in params else "%Y%m%dT%H%M%S"
            return eastern(dt.datetime.strptime(v, fmt))

        unesc = lambda s: s.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
        out.append({
            "name": unesc(f.get("SUMMARY", ("", []))[0]),
            "start": when("DTSTART"),
            "end": when("DTEND"),
            "description": unesc(f.get("DESCRIPTION", ("", []))[0]),
            "location": unesc(f.get("LOCATION", (DEFAULT_LOCATION, []))[0]) or DEFAULT_LOCATION,
            "url": f.get("URL", (LIST, []))[0],
            "image": f.get("ATTACH", ("", []))[0],
        })
    return out


# ---------- source 2: JSON-LD on list pages ----------
LD_RE = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)


def walk_events(obj):
    if isinstance(obj, list):
        for x in obj:
            yield from walk_events(x)
    elif isinstance(obj, dict):
        t = obj.get("@type")
        if t == "Event" or (isinstance(t, list) and "Event" in t):
            yield obj
        for k in ("@graph", "itemListElement", "item"):
            if k in obj:
                yield from walk_events(obj[k])


def events_from_jsonld(session, pages):
    out = []
    for n in range(1, pages + 1):
        url = LIST if n == 1 else f"{LIST}page/{n}/"
        r = session.get(url, timeout=30)
        if r.status_code == 404:
            break
        r.raise_for_status()
        found = 0
        for blob in LD_RE.findall(r.text):
            try:
                data = json.loads(blob.strip())
            except json.JSONDecodeError:
                continue
            for e in walk_events(data):
                if not e.get("startDate"):
                    continue
                img = e.get("image")
                if isinstance(img, dict):
                    img = img.get("url")
                elif isinstance(img, list):
                    img = img[0] if img else ""
                out.append({
                    "name": html.unescape(e.get("name", "")),
                    "start": parse_iso(e["startDate"]),
                    "end": parse_iso(e["endDate"]) if e.get("endDate") else None,
                    "description": strip_html(e.get("description", "")),
                    "location": location_str(e.get("location")),
                    "url": e.get("url") or LIST,
                    "image": img or "",
                })
                found += 1
        print(f"page {n}: {found} events", file=sys.stderr)
        if not found:
            break
    return out


# ---------- output ----------
def write_ics(events, path):
    stamp = utc(dt.datetime.now(dt.timezone.utc))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//sheplibrary.org//Events//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:Shepherdstown Public Library Calendar",
             "X-WR-TIMEZONE:America/New_York"]

    seen = set()
    for e in sorted(events, key=lambda e: e["start"]):
        key = (e["name"], e["start"])
        if key in seen:
            continue
        seen.add(key)
        end = e["end"] or e["start"] + dt.timedelta(hours=1)
        uid = hashlib.sha1(f"{e['name']}|{utc(e['start'])}".encode()).hexdigest()
        lines += [
            "BEGIN:VEVENT",
            f"UID:{local_z(e['start'])}-{uid}@sheplibrary",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{local_z(e['start'])}",
            f"DTEND:{local_z(end)}",
            f"SUMMARY:{esc(e['name'])}",
            f"LOCATION:{e['location']}",
            f"DESCRIPTION:{esc(e['description'])}",
            f"CATEGORIES:{CATEGORY}",
            f"ORGANIZATION:{ORG}",
            f"URL:{e['url']}",
            "STATUS:CONFIRMED",
            "SOURCE:sheplibrary.org/",
        ]
        if e["image"]:
            lines.append(f"IMAGE_URL:{e['image']}")
        lines += ["SEQUENCE:0", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(seen)} events to {path}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pages", type=int, default=5, help="max list pages (JSON-LD mode)")
    p.add_argument("--source", choices=["auto", "ical", "jsonld"], default="auto")
    p.add_argument("--months", type=int, default=3,
                   help="how far ahead to collect (iCal mode)")
    p.add_argument("-o", "--output", default="sheplibrary.ics")
    args = p.parse_args()

    today = datetime.today()
    today_formatted = today.strftime("%Y%m%d")
    output_file = 'library_' + today_formatted + '.ics'

    num_months = 2

    s = requests.Session()
    s.headers.update(HEADERS)
    until = dt.date.today() + dt.timedelta(days=31 * num_months)

    events = []
    if args.source in ("auto", "ical"):
        events = ical_all(s, until)
        if not events and args.source == "ical":
            sys.exit("iCal export not available")
    if not events:
        events = events_from_jsonld(s, args.pages)
    if not events:
        sys.exit("No events found -- run with the page saved and send it to Claude")
    write_ics(events, output_file)


if __name__ == "__main__":
    main()