#!/usr/bin/env python3
"""
Experience Shepherdstown "Live Music" page -> .ics
https://shepherdstown.info/listing/live-music/

The page is hand-typed WordPress content:
    <h2>Sunday, 10/18</h2>
    <p><strong>7:30pm – Open Mic</strong> | <a href="...">The Study Hall Sports Pub</a></p>
so we walk the content in order, track the current date heading, and parse
"TIME – NAME | VENUE" lines under it.

Usage:
  python3 livemusic_ics.py -o livemusic.ics
  python3 livemusic_ics.py --html saved_page.html      # parse a saved copy
"""
import argparse
import datetime as dt
import hashlib
import re
import sys
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from datetime import datetime, timedelta
from datetime import date

URL = "https://shepherdstown.info/listing/live-music/"
EASTERN = ZoneInfo("America/New_York")
REST = "https://shepherdstown.info/wp-json/wp/v2/pages?slug=live-music&_fields=content"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://shepherdstown.info/",
    "Upgrade-Insecure-Requests": "1",
}
DEFAULT_MINUTES = 120  # when only a start time is given

DATE_RE = re.compile(
    r"^\s*(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?",
    re.I)
TIME = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)"
LINE_RE = re.compile(
    rf"^\s*{TIME}\s*(?:[-–—]|to)\s*{TIME}?\s*[-–—]\s*(.+)$"      # 7:30pm-9:00pm – Name | Venue
    rf"|^\s*{TIME}\s*[-–—]\s*(.+)$", re.I)                        # 7:30pm – Name | Venue


def parse_time(s, ampm_hint=None):
    s = s.strip().lower().replace(" ", "")
    if s == "noon":
        return dt.time(12, 0)
    if s == "midnight":
        return dt.time(0, 0)
    m = re.match(r"(\d{1,2})(?::(\d{2}))?(am|pm)?$", s)
    if not m:
        return None
    h, mi, ap = int(m[1]), int(m[2] or 0), m[3] or ampm_hint
    if ap == "pm" and h != 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return dt.time(h % 24, mi)


def ampm(s):
    m = re.search(r"(am|pm)", s or "", re.I)
    return m[1].lower() if m else None


def infer_year(month, day, today):
    """No year on the page: pick the year that puts the date nearest today
    (handles December -> January rollover)."""
    best = None
    for y in (today.year - 1, today.year, today.year + 1):
        try:
            d = dt.date(y, month, day)
        except ValueError:
            continue
        if best is None or abs((d - today).days) < abs((best - today).days):
            best = d
    return best


def local_z(d):
    # Eastern wall-clock with Z -- same convention as the other feeds
    return d.astimezone(EASTERN).strftime("%Y%m%dT%H%M%S")


def esc(s):
    return (str(s).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def block_lines(el):
    """Split a block element into text lines at <br>, keeping the first link."""
    lines, buf, link = [], [], None

    def flush():
        nonlocal buf, link
        text = re.sub(r"\s+", " ", "".join(buf)).strip()
        if text:
            lines.append((text, link))
        buf, link = [], None

    def walk(node):
        nonlocal link
        for c in node.children:
            if isinstance(c, NavigableString):
                buf.append(str(c))
            elif isinstance(c, Tag):
                if c.name == "br":
                    flush()
                else:
                    if c.name == "a" and link is None and c.get("href"):
                        link = c["href"]
                    walk(c)
    walk(el)
    flush()
    return lines


def parse(html, today=None):
    today = today or dt.date.today()
    soup = BeautifulSoup(html, "html.parser")
    root = (soup.select_one(".entry-content") or soup.select_one("article")
            or soup.select_one("main") or soup.body or soup)
    events, current = [], None
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "div"]):
        if el.name == "div" and el.find(["p", "h2", "h3", "li", "div"]):
            continue  # only leaf-ish divs
        if el.find_parent("li") and el.name != "li":
            continue
        text = el.get_text(" ", strip=True)
        dm = DATE_RE.match(text)
        if dm and (el.name.startswith("h") or len(text) < 40):
            y = int(dm[3]) if dm[3] else None
            if y and y < 100:
                y += 2000
            current = (dt.date(y, int(dm[1]), int(dm[2])) if y
                       else infer_year(int(dm[1]), int(dm[2]), today))
            continue
        if current is None:
            continue
        for line, link in block_lines(el):
            m = LINE_RE.match(line)
            if not m:
                continue
            if m[1]:
                t1s, t2s, rest = m[1], m[2], m[3]
            else:
                t1s, t2s, rest = m[4], None, m[5]
            # "7-9pm": start inherits the end's am/pm
            t1 = parse_time(t1s, ampm(t1s) or ampm(t2s))
            t2 = parse_time(t2s, ampm(t2s)) if t2s else None
            if t1 is None:
                continue
            name, _, venue = rest.partition("|")
            start = dt.datetime.combine(current, t1, EASTERN)
            if t2:
                end = dt.datetime.combine(current, t2, EASTERN)
                if end <= start:
                    end += dt.timedelta(days=1)  # runs past midnight
            else:
                end = start + dt.timedelta(minutes=DEFAULT_MINUTES)
            # print(170, 'name:', name, 'venue:', venue)
            events.append({
                "name": name.strip(" –—-"),
                "venue": venue.strip() or "Shepherdstown",
                "start": start, "end": end,
                "url": link or URL,
            })
    return events


def write_ics(events, path):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//shepherdstown.info/listing/live-music//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:Shepherdstown Live Music Calendar",
             "X-WR-TIMEZONE:America/New_York"]
    seen = set()
    for e in sorted(events, key=lambda e: e["start"]):
        key = (e["name"], e["start"])
        if key in seen or \
        "O’Hurley" in e['name'] or "O’Hurley" in e['venue'] or \
        "Shepherdstown Opera House" in e['venue'] or \
        "Shepherd Univ" in e['venue']:
            continue
        seen.add(key)
        h = hashlib.sha1(f"{e['name']}|{e['venue']}".encode()).hexdigest()[:16]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{local_z(e['start'])}-{h}@livemusic",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{local_z(e['start'])}",
            f"DTEND:{local_z(e['end'])}",
            f"SUMMARY:{esc(e['name'])}",
            f"LOCATION:{e['venue']}",
            f"DESCRIPTION:{esc(e['name'] + ' at ' + e['venue'])}",
            "CATEGORIES:Music & Film & Stage",
            f"ORGANIZATION:{e['venue']}",
            f"URL:{e['url']}",
            "STATUS:CONFIRMED",
            "SOURCE:shepherdstown.info/listing/live-music/",
            "SEQUENCE:0",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {len(seen)} events to {path}", file=sys.stderr)


def fetch():
    """Try progressively more browser-like ways to get the page."""
    # 1. plain request with full browser headers
    try:
        r = requests.get(URL, headers=HEADERS, timeout=30)
        if r.ok:
            print("fetched: page (requests)", file=sys.stderr)
            return r.text
        print(f"page via requests: HTTP {r.status_code}", file=sys.stderr)
    except requests.RequestException as e:
        print(f"page via requests: {e}", file=sys.stderr)

    # 2. WordPress's own JSON copy of the page content
    try:
        r = requests.get(REST, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
        if r.ok and r.json():
            print("fetched: WordPress REST API", file=sys.stderr)
            return r.json()[0]["content"]["rendered"]
        print(f"REST API: HTTP {r.status_code}", file=sys.stderr)
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        print(f"REST API: {e}", file=sys.stderr)

    # 3. curl_cffi: same request, but with Chrome's network fingerprint
    try:
        from curl_cffi import requests as creq
    except ImportError:
        sys.exit("Blocked. Install curl_cffi (pip install curl_cffi) and rerun, "
                 "or save the page in your browser and use --html.")
    r = creq.get(URL, impersonate="chrome", timeout=30)
    if r.status_code == 200:
        print("fetched: page (curl_cffi)", file=sys.stderr)
        return r.text
    sys.exit(f"Still blocked (HTTP {r.status_code}). Save the page in your "
             "browser and run with --html saved_page.html.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", default="livemusic.ics")
    p.add_argument("--html", help="parse a saved HTML file instead of fetching")
    args = p.parse_args()

    today = datetime.today()
    today_formatted = today.strftime("%Y%m%d")
    output_file = 'livemusic_' + today_formatted + '.ics'

    if args.html:
        html = open(args.html, encoding="utf-8").read()
    else:
        html = fetch()
    events = parse(html)
    if not events:
        sys.exit("No events parsed -- save the page and send it to Claude")
    write_ics(events, output_file)


if __name__ == "__main__":
    main()