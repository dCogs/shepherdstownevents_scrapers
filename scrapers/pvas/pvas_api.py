#!/usr/bin/env python3
"""
The Events Calendar (WordPress plugin) sites -> .ics

Works for any site running The Events Calendar. Tries, in order:
  1. The plugin's iCal export (?ical=1), paged past its 30-event cap
  2. The schema.org JSON-LD blocks embedded in each list page

Times are read as Eastern clock time (whatever offset the feed claims)
and written as Eastern clock time with a Z, matching the other feeds.

Usage:
  python3 tec_ics.py --site audubon -o audubon.ics
  python3 tec_ics.py --site sheplibrary --months 6 -o sheplibrary.ics
  python3 tec_ics.py --site audubon --source jsonld --pages 10
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys

import requests

SITES = {
    "sheplibrary": dict(
        base="https://www.sheplibrary.org", list_path="/events/list/",
        org="Shepherdstown Public Library",
        default_location="Shepherdstown Public Library, 145 S Princess St, Shepherdstown",
        category="Library", calname="Shepherdstown Public Library Calendar",
        tag="sheplibrary", source="sheplibrary.org/",
        output="sheplibrary.ics"),
    "audubon": dict(
        base="https://www.potomacaudubon.org", list_path="/calendar/list/",
        org="Potomac Valley Audubon Society",
        default_location="",
        category="Nature", calname="Potomac Valley Audubon Calendar",
        tag="potomacaudubon", source="potomacaudubon.org/calendar/",
        output="audubon.ics", browser=True),
}

# set from the chosen --site in main()
BASE = LIST = ORG = DEFAULT_LOCATION = CATEGORY = CALNAME = TAG = SOURCE = None


def configure(site):
    global BASE, LIST, ORG, DEFAULT_LOCATION, CATEGORY, CALNAME, TAG, SOURCE
    c = SITES[site]
    BASE = c["base"]
    LIST = BASE + c["list_path"]
    ORG, DEFAULT_LOCATION, CATEGORY = c["org"], c["default_location"], c["category"]
    CALNAME, TAG, SOURCE = c["calname"], c["tag"], c["source"]
    return c
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
}


# ---------- helpers ----------
def utc(d):
    return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")



def local_z(d):
    """Eastern clock time written with a Z, matching ghost.ics
    (a 7pm event -> T190000Z) and what the importer expects."""
    return eastern_now(d).strftime("%Y%m%dT%H%M%SZ")


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
    """Some feeds (the library's) label Eastern clock times as UTC, so drop whatever
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


# ---------- fetching (with Cloudflare fallback) ----------
CF_MARKERS = ("Performing security verification", "cf-challenge", "challenge-platform",
              "Just a moment...")


def blocked(r):
    return r.status_code in (403, 503) and any(m in r.text for m in CF_MARKERS)


USE_BROWSER = False
_PW = None  # (playwright, context) once started


class _Resp:
    def __init__(self, status, text):
        self.status_code, self.text, self.ok = status, text, 200 <= status < 300


def browser_get(url, params=None):
    """Fetch through a real Chrome window: Chrome passes Cloudflare's
    JavaScript check, and later requests reuse its clearance cookie."""
    global _PW
    import time
    import urllib.parse
    if _PW is None:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        profile = os.path.expanduser("~/.cache/tec_ics_chrome")
        # headed (visible) Chrome: Cloudflare usually rejects headless browsers
        ctx = pw.chromium.launch_persistent_context(
            profile, channel="chrome", headless=False,
            args=["--window-size=800,600"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(LIST, wait_until="domcontentloaded", timeout=60000)
        print("browser: if Cloudflare asks you to verify you're human, click it "
              "in the Chrome window (waiting up to 2 minutes)", file=sys.stderr)
        for _ in range(120):
            if not any(m in page.content() for m in CF_MARKERS):
                break
            time.sleep(1)
        else:
            sys.exit("Cloudflare check wasn't completed within 2 minutes.")
        print("browser: Cloudflare check passed", file=sys.stderr)
        _PW = (pw, ctx)
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    r = _PW[1].request.get(full, timeout=60000)
    return _Resp(r.status, r.text())


def close_browser():
    if _PW:
        _PW[1].close()
        _PW[0].stop()


def get(session, url, params=None):
    """requests -> curl_cffi (Chrome fingerprint) -> real Chrome (--browser)."""
    if USE_BROWSER and _PW:
        return browser_get(url, params)
    r = session.get(url, params=params, timeout=30)
    if not blocked(r):
        return r
    try:
        from curl_cffi import requests as creq
        r2 = creq.get(url, params=params, impersonate="chrome", timeout=30)
        if r2.status_code == 200 and not any(m in r2.text for m in CF_MARKERS):
            return r2
    except ImportError:
        pass
    if USE_BROWSER:
        return browser_get(url, params)
    sys.exit("Cloudflare's JavaScript challenge is blocking this site. "
             "Rerun with --browser (needs: pip install playwright, and Google Chrome).")


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
            r = get(session, url, params)
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
        r = get(session, url)
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


# ---------- output (same layout as ghost.ics) ----------
def write_ics(events, path):
    stamp = utc(dt.datetime.now(dt.timezone.utc))
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//potomacaudubon.org//calendar//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{CALNAME}",
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
            f"UID:{local_z(e['start'])}-{uid}@{TAG}",
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
            f"SOURCE:{SOURCE}",
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
    p.add_argument("--site", choices=sorted(SITES), required=True)
    p.add_argument("--pages", type=int, default=5, help="max list pages (JSON-LD mode)")
    p.add_argument("--source", choices=["auto", "ical", "jsonld"], default="auto")
    p.add_argument("--months", type=int, default=3,
                   help="how far ahead to collect (iCal mode)")
    p.add_argument("-o", "--output", help="default: <site>.ics")
    p.add_argument("--ical-file", nargs="+", metavar="FILE",
                   help="parse .ics file(s) you downloaded yourself; no fetching")
    p.add_argument("--browser", action="store_true",
                   help="if Cloudflare blocks, fetch through a real Chrome window")
    args = p.parse_args()
    cfg = configure(args.site)
    global USE_BROWSER
    USE_BROWSER = args.browser or cfg.get("browser", False)
    args.output = args.output or cfg["output"]

    s = requests.Session()
    s.headers.update(HEADERS)
    until = dt.date.today() + dt.timedelta(days=31 * args.months)

    events = []
    if args.ical_file:
        seen = set()
        for path in args.ical_file:
            with open(path, encoding="utf-8") as f:
                for e in events_from_ical(f.read()):
                    if e["start"] and (e["name"], e["start"]) not in seen:
                        seen.add((e["name"], e["start"]))
                        events.append(e)
        write_ics(events, args.output)
        return
    if args.source in ("auto", "ical"):
        events = ical_all(s, until)
        if not events and args.source == "ical":
            sys.exit("iCal export not available")
    if not events:
        events = events_from_jsonld(s, args.pages)
    if not events:
        sys.exit("No events found -- run with the page saved and send it to Claude")
    write_ics(events, args.output)


if __name__ == "__main__":
    try:
        main()
    finally:
        close_browser()