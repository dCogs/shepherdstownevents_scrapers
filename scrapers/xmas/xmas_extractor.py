#!/usr/bin/env python3
"""
Experience Shepherdstown "Holidays in Shepherdstown 2026" page -> .ics
https://shepherdstown.info/holidays-in-shepherdstown-2026/

The page is hand-typed WordPress content:
    <h2><strong>❄️ Saturday, November 21st</strong></h2>
    <p><strong>11am-5pm — <a href="...">Handmade Christmas</a></strong><br>
       Optional description line(s)<br>
       <em>102 E German St</em></p>
An event starts at a bold "TIME — NAME" line; following lines belong to it
until the next event or heading. The first italic line (or line that looks
like a street address) is the venue; everything else is description.
"All Day" / "Time TBD" entries become all-day events.

Usage:
  python3 xmas_extractor.py
  python3 xmas_extractor.py --html saved_page.html      # parse a saved copy
"""
import argparse
import datetime as dt
import hashlib
import re
import sys
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

URL = "https://shepherdstown.info/holidays-in-shepherdstown-2026/"
EASTERN = ZoneInfo("America/New_York")
REST = "https://shepherdstown.info/wp-json/wp/v2/pages?slug=holidays-in-shepherdstown-2026&_fields=content"
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

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# "Saturday, November 21st"  or  "Sunday, 10/18"  (emoji/prefix allowed)
DATE_RE = re.compile(
    r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+"
    r"(?:([a-z]{3})[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?"
    r"|(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?)",
    re.I)

TIME = r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)"
EVENT_RE = re.compile(
    rf"^\s*(?:(?P<t1>{TIME})\s*(?:[-–—]|to)\s*(?P<t2>{TIME})"   # 11am-5pm
    rf"|(?P<t0>{TIME})"                                          # 7pm
    r"|(?P<allday>all[\s-]*day|time\s*tbd|tbd))"                 # All Day / Time TBD
    r"\s*[-–—]\s*(?P<rest>.+)$", re.I)

ADDR_RE = re.compile(
    r"\b\d+\s+(?:[NSEW]\.?\s+)?[A-Z][a-z]+\.?\s+"
    r"(?:St|Street|Ln|Lane|Dr|Drive|Ave|Avenue|Rd|Road|Way|Pike)\b")


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


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


def match_date(text, today):
    m = DATE_RE.search(text)
    if not m:
        return None
    if m[1]:
        month = MONTHS.get(m[1].lower())
        if not month:
            return None
        day, year = int(m[2]), m[3]
    else:
        month, day, year = int(m[4]), int(m[5]), m[6]
    if year:
        y = int(year)
        y = y + 2000 if y < 100 else y
        try:
            return dt.date(y, month, day)
        except ValueError:
            return None
    return infer_year(month, day, today)


def local_z(d):
    # Eastern wall-clock, no TZID -- same convention as the other feeds
    return d.strftime("%Y%m%dT%H%M%S")


def esc(s):
    return (str(s).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def block_lines(el):
    """Split a block element into lines at <br>. For each line keep the full
    text, the bold text, the non-bold text, the italic text, and a link
    (preferring one inside the bold part)."""
    lines = []

    def new():
        return {"all": [], "strong": [], "plain": [], "em": [],
                "slink": None, "link": None}
    cur = new()

    def flush():
        nonlocal cur
        text = norm("".join(cur["all"]))
        if text:
            lines.append({
                "text": text,
                "strong": norm("".join(cur["strong"])),
                "plain": norm("".join(cur["plain"])),
                "em": norm("".join(cur["em"])),
                "link": cur["slink"] or cur["link"],
            })
        cur = new()

    def walk(node, strong, em):
        for c in node.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                s = str(c)
                cur["all"].append(s)
                # a space in the "other" buckets keeps words from fusing
                cur["strong" if strong else "plain"].append(s)
                cur["plain" if strong else "strong"].append(" ")
                cur["em"].append(s if em else " ")
            elif isinstance(c, Tag):
                if c.name == "br":
                    flush()
                    continue
                if c.name == "a" and c.get("href"):
                    if strong or c.find(["strong", "b"]):
                        cur["slink"] = cur["slink"] or c["href"]
                    cur["link"] = cur["link"] or c["href"]
                walk(c, strong or c.name in ("strong", "b"),
                     em or c.name in ("em", "i"))
    walk(el, False, False)
    flush()
    return lines


def is_venue(ln):
    t = ln["text"]
    return bool(ln["em"]) and ln["em"] == t or bool(ADDR_RE.search(t))


def finish(ev):
    """Turn an accumulated event into start/end and clean up the name."""
    name = ev["name"]
    flags = re.search(r"(?:\s+[*$])+\s*$", name)
    notes = []
    if flags:
        if "*" in flags[0]:
            notes.append("18+ or 21+")
        if "$" in flags[0]:
            notes.append("Has a cost")
        name = name[:flags.start()]
    name = name.strip(" –—-:")

    m, day = ev["m"], ev["date"]
    if m["allday"]:
        start, end, allday = day, day + dt.timedelta(days=1), True
        if "tbd" in m["allday"].lower():
            notes.insert(0, "Time TBD")
    else:
        allday = False
        if m["t1"]:
            t2 = parse_time(m["t2"])
            t1 = parse_time(m["t1"], ampm(m["t1"]) or ampm(m["t2"]))
            if t1 and t2 and not ampm(m["t1"]) and t1 > t2:
                t1 = parse_time(m["t1"], "am")       # "11-1pm" -> 11am
        else:
            t1, t2 = parse_time(m["t0"]), None
        start = dt.datetime.combine(day, t1, EASTERN)
        if t2:
            end = dt.datetime.combine(day, t2, EASTERN)
            if end <= start:
                end += dt.timedelta(days=1)         # runs past midnight
        else:
            end = start + dt.timedelta(minutes=DEFAULT_MINUTES)

    desc = list(ev["desc"])
    if ev["section"]:
        desc.append(f"Part of {ev['section']}")
    desc += notes
    return {
        "name": name,
        "venue": (ev["venue"] or "Shepherdstown").rstrip(". "),
        "start": start, "end": end, "allday": allday,
        "desc": desc,
        "url": ev["link"] or URL,
    }


def parse(html, today=None):
    today = today or dt.date.today()
    soup = BeautifulSoup(html, "html.parser")
    root = (soup.select_one(".entry-content") or soup.select_one("article")
            or soup.select_one("main") or soup.body or soup)
    events, day, section, ev = [], None, None, None

    def close():
        nonlocal ev
        if ev:
            events.append(finish(ev))
            ev = None

    for el in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "div"]):
        if el.name == "div" and el.find(["p", "h2", "h3", "li", "div"]):
            continue  # only leaf-ish divs
        if el.find_parent("li") and el.name != "li":
            continue
        if el.find_parent(["footer", "nav", "aside", "header"]):
            continue
        text = norm(el.get_text(" ", strip=True))
        heading = el.name[0] == "h" and el.name[1:].isdigit()
        d = match_date(text, today) if (heading or len(text) < 40) else None
        if d:
            close()
            day, section = d, None
            continue
        if heading:
            close()
            section = text.strip(" :")
            continue
        if day is None:
            continue
        for ln in block_lines(el):
            m = EVENT_RE.match(ln["strong"]) if ln["strong"] else None
            if m and EVENT_RE.match(ln["text"]):
                close()
                ev = {"date": day, "m": m, "name": m["rest"], "venue": None,
                      "desc": [], "link": ln["link"], "section": section}
                extra = ln["plain"].strip(" ,–—-|")
                if extra:
                    if ADDR_RE.search(extra) or ln["em"] == extra:
                        ev["venue"] = extra
                    else:
                        ev["desc"].append(extra)
            elif ev:
                if ev["venue"] is None and is_venue(ln):
                    ev["venue"] = ln["text"]
                else:
                    ev["desc"].append(ln["text"])
    close()
    return events


def organization(venue):
    """'Mohalu Wellness, 126 W German St' -> 'Mohalu Wellness'.
    A bare address ('102 E German St') is kept as-is."""
    name = venue.split(",", 1)[0].strip()
    if re.match(r"\d", name):
        return venue
    name = re.sub(r"^(?:in front of|inside|upstairs at|outside)\s+(?:the\s+)?",
                  "", name, flags=re.I)
    return name or venue


def write_ics(events, path):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//shepherdstown.info/holidays-in-shepherdstown-2026//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:Shepherdstown Christmas Calendar",
             "X-WR-TIMEZONE:America/New_York"]
    seen = set()
    for e in sorted(events, key=lambda e: (e["start"].isoformat()[:10],
                                           not e["allday"], e["start"].isoformat())):
        key = (e["name"], str(e["start"]))
        if key in seen or \
        "O’Hurley" in e['name'] or "O’Hurley" in e['venue'] or \
        "Shepherdstown Opera House" in e['venue'] or \
        "Shepherd Univ" in e['venue'] or \
        "S King St" in e['venue']:
            continue
        seen.add(key)
        h = hashlib.sha1(f"{e['name']}|{e['venue']}".encode()).hexdigest()[:16]
        if e["allday"]:
            ds = e["start"].strftime("%Y%m%d")
            when = [f"DTSTART;VALUE=DATE:{ds}",
                    f"DTEND;VALUE=DATE:{e['end'].strftime('%Y%m%d')}"]
        else:
            ds = local_z(e["start"])
            when = [f"DTSTART:{ds}", f"DTEND:{local_z(e['end'])}"]
        desc = "\n".join(e["desc"] + [f"{e['name']} at {e['venue']}"])
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ds}-{h}@xmas",
            f"DTSTAMP:{stamp}",
            *when,
            f"SUMMARY:{esc(e['name'])}",
            f"LOCATION:{esc(e['venue'])}",
            f"DESCRIPTION:{esc(desc)}",
            "CATEGORIES:Holidays & Fairs",
            f"ORGANIZATION:{esc(organization(e['venue']))}",
            f"URL:{e['url']}",
            "STATUS:CONFIRMED",
            "SOURCE:shepherdstown.info/holidays-in-shepherdstown-2026/",
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
    p.add_argument("-o", "--output", help="output path (default xmas_YYYYMMDD.ics)")
    p.add_argument("--html", help="parse a saved HTML file instead of fetching")
    args = p.parse_args()

    output_file = args.output or f"xmas_{dt.date.today():%Y%m%d}.ics"

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