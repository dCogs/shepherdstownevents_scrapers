#!/usr/bin/env python3
"""
Fetch events from a The Events Calendar (WordPress) REST API and write an .ics file.

Standard library only.

Usage:
    python3 sheplibrary_ics.py                         # today + 90 days -> sheplibrary.ics
    python3 sheplibrary_ics.py --days 180 -o lib.ics
    python3 sheplibrary_ics.py --start 2026-11-01 --end 2027-01-31
    python3 sheplibrary_ics.py --json events.json events2.json   # saved from browser
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.sheplibrary.org/wp-json/tribe/events/v1/events"
UID_DOMAIN = "sheplibrary.org"
CAL_NAME = "Shepherdstown Public Library"
TZID = "America/New_York"
VTIMEZONE = [
    "BEGIN:VTIMEZONE", f"TZID:{TZID}",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0400", "TZNAME:EDT",
    "DTSTART:20070311T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:-0400", "TZOFFSETTO:-0500", "TZNAME:EST",
    "DTSTART:20071104T020000", "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "END:STANDARD",
    "END:VTIMEZONE",
]
UA = "Mozilla/5.0 (X11; Linux x86_64) sheplibrary-ics/1.0"


# ---------- fetching ----------

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "replace")
        ctype = r.headers.get("Content-Type", "")
    if "json" not in ctype and not body.lstrip().startswith("{"):
        sys.exit(f"Got non-JSON response from {url} (probably the captcha/challenge page).\n"
                 f"First 200 chars:\n{body[:200]}")
    return json.loads(body)


def fetch_events(start, end):
    params = {"start_date": f"{start} 00:00:00", "end_date": f"{end} 23:59:59",
              "per_page": 100, "status": "publish"}
    url = BASE + "?" + urllib.parse.urlencode(params)
    events, seen = [], set()
    while url:
        try:
            data = fetch_json(url)
        except urllib.error.HTTPError as e:
            if e.code == 404 and events:   # past the last page
                break
            raise
        for ev in data.get("events", []):
            if ev["id"] not in seen:
                seen.add(ev["id"])
                events.append(ev)
        url = data.get("next_rest_url")
    return events


def load_json_files(paths):
    events, seen = [], set()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if "events" not in data:
            sys.exit(f"{p}: no 'events' key - is this the API output?")
        for ev in data["events"]:
            if ev["id"] not in seen:
                seen.add(ev["id"])
                events.append(ev)
        if data.get("next_rest_url"):
            print(f"Note: {p} has more pages. Next one:\n  {data['next_rest_url']}",
                  file=sys.stderr)
    return events


# ---------- ICS formatting ----------

def strip_html(s):
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def esc(s):
    return (s.replace("\\", "\\\\").replace(";", "\\;")
             .replace(",", "\\,").replace("\r\n", "\n").replace("\n", "\\n"))


def fold(line):
    """Fold to 75 octets per RFC 5545 without splitting UTF-8 characters."""
    out, cur, size = [], "", 0
    limit = 75
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > limit:
            out.append(cur)
            cur, size, limit = " ", 1, 75
        cur += ch
        size += n
    out.append(cur)
    return "\r\n".join(out)


def utc_stamp(s):
    # "2026-10-16 15:00:00" (UTC) -> "20261016T150000Z"
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%dT%H%M%SZ")


def local_stamp(s):
    # "2026-10-20 18:00:00" (site-local wall time) -> "20261020T180000"
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%dT%H%M%S")


def location(ev):
    v = ev.get("venue")
    if not isinstance(v, dict) or not v:
        return ""
    parts = [v.get("venue"), v.get("address"), v.get("city"),
             v.get("stateprovince") or v.get("state") or v.get("province"), v.get("zip")]
    return ", ".join(html.unescape(p) for p in parts if p)


def vevent(ev, now):
    lines = ["BEGIN:VEVENT",
             f"UID:tec-{ev['id']}@{UID_DOMAIN}",
             f"DTSTAMP:{now}"]
    if ev.get("all_day"):
        sd = dt.date.fromisoformat(ev["start_date"][:10])
        ed = dt.date.fromisoformat(ev["end_date"][:10]) + dt.timedelta(days=1)  # DTEND exclusive
        lines += [f"DTSTART;VALUE=DATE:{sd:%Y%m%d}", f"DTEND;VALUE=DATE:{ed:%Y%m%d}"]
    else:
        lines += [f"DTSTART;TZID={TZID}:{local_stamp(ev['start_date'])}",
                  f"DTEND;TZID={TZID}:{local_stamp(ev['end_date'])}"]
    lines.append(f"SUMMARY:{esc(html.unescape(ev.get('title', '')))}")
    desc = strip_html(ev.get("description", ""))
    if ev.get("cost"):
        desc = f"Cost: {ev['cost']}\n\n{desc}"
    if desc:
        lines.append(f"DESCRIPTION:{esc(desc)}")
    loc = location(ev)
    if loc:
        lines.append(f"LOCATION:{esc(loc)}")
    if ev.get("url"):
        lines.append(f"URL:{ev['url']}")
    cats = [html.unescape(c["name"]) for c in ev.get("categories") or [] if c.get("name")]
    if cats:
        lines.append("CATEGORIES:" + ",".join(esc(c) for c in cats))
    if ev.get("modified_utc"):
        lines.append(f"LAST-MODIFIED:{utc_stamp(ev['modified_utc'])}")
    lines.append("END:VEVENT")
    return lines


def build_ics(events, do_fold=True):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//sheplibrary-ics//EN", "CALSCALE:GREGORIAN",
             f"X-WR-CALNAME:{esc(CAL_NAME)}", f"X-WR-TIMEZONE:{TZID}"] + VTIMEZONE
    for ev in events:
        lines += vevent(ev, now)
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) if do_fold else l for l in lines) + "\r\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=dt.date.today().isoformat(), help="YYYY-MM-DD (default today)")
    ap.add_argument("--end", help="YYYY-MM-DD (overrides --days)")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("-o", "--out", default="sheplibrary.ics")
    ap.add_argument("--json", nargs="+", metavar="FILE",
                    help="read saved API JSON page(s) instead of fetching")
    ap.add_argument("--no-fold", action="store_true",
                    help="don't fold long lines at 75 octets (for simple line-based readers)")
    a = ap.parse_args()

    if a.json:
        events = load_json_files(a.json)
        what = f"from {len(a.json)} file(s)"
    else:
        end = a.end or (dt.date.fromisoformat(a.start) + dt.timedelta(days=a.days)).isoformat()
        events = fetch_events(a.start, end)
        what = f"({a.start} to {end})"

    events.sort(key=lambda e: e.get("start_date") or "")
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write(build_ics(events, do_fold=not a.no_fold))
    print(f"Wrote {len(events)} events {what} to {a.out}")


if __name__ == "__main__":
    main()
