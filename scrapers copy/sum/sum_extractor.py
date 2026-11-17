#!/usr/bin/env python3
"""
Shepherd University School of Music Extractor (ICS feed version)

Instead of rendering the embedded Google Calendar in a browser and parsing
the visible text, this pulls each calendar's public iCalendar feed directly.
Titles, times and locations come from structured fields, so there is
nothing to mis-parse.

Requirements:
    pip install requests icalendar recurring-ical-events
"""

import uuid
from datetime import datetime, date, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
import icalendar
import recurring_ical_events

TZ = ZoneInfo("America/New_York")
today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
last_date = today + timedelta(days=180)
today_formatted = today.strftime("%Y%m%d")

# Calendar IDs decoded from the src= parameters of the embed URL on
# https://www.shepherd.edu/music/calendar-of-concerts
CALENDAR_IDS = [
    "s1sjjaa0lbgjkkf87manbrpa74@group.calendar.google.com",
    "dmnc1ajkbc2dl98b3magton81k@group.calendar.google.com",
    "n3kvlg32s84c4ug8srs5lr1lq8@group.calendar.google.com",
    "8ktbfn44012k4up12tho4vdikk@group.calendar.google.com",
    "hiep7ubgcgr8d6gncn57jstbeo@group.calendar.google.com",
    "1t32kgfhrf92fe0gdd7sr9rud4@group.calendar.google.com",
    "fop32dcqpqdc0qfhfhlt17ou20@group.calendar.google.com",
    "c3027ltqjcbuk1pak8ticjgdeo@group.calendar.google.com",
    "sbvd33hvb7vkedu419atrkhguk@group.calendar.google.com",
    "sb971r5dnqjdt0nf6c8k61bdb4@group.calendar.google.com",
    "7cofu68af7b4ho1643f1acqbu8@group.calendar.google.com",
    "ihghs2qsm5d0n4q3skufi7lmgo@group.calendar.google.com",
]
FEED_URL = "https://calendar.google.com/calendar/ical/{}/public/basic.ics"

FRANK = "Frank Arts Center 260 University Dr, Shepherdstown, WV 25443"
SKIP = ["RAM PEP BAND", "RAM BAND CAMP", "STRING CAMP", "HOME FOOTBALL GAME",
        "RB EXHIBITION", "SUMMER CLINIC", "REHEARSAL", "RAM BAND TOUR"]


def default_location(title):
    t = title.lower()
    if "parade" in t:
        return "Shepherdstown"
    return FRANK if "salon series" in t else "Shepherd University"


def pick_location(location, title, calname):
    """Same defaults as the browser version: no venue -> Frank Arts Center
    for concerts, title-based default for marching band calendars."""
    if location:
        return location
    if "marching band" in calname.lower() or "parade" in title.lower():
        return default_location(title)
    return FRANK


def fmt(dt):
    """Local floating time, YYYYMMDDTHHMMSS, matching the old output."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(TZ)
    return dt.strftime("%Y%m%dT%H%M%S")


def fetch_calendar(cal_id):
    resp = requests.get(FEED_URL.format(quote(cal_id)), timeout=30)
    resp.raise_for_status()
    return icalendar.Calendar.from_ical(resp.content)


def extract_events(cal, seen):
    calname = str(cal.get("X-WR-CALNAME", ""))
    out = []
    # .between() expands recurring events (RRULE/EXDATE) into instances
    for ev in recurring_ical_events.of(cal).between(today, last_date):
        if str(ev.get("STATUS", "")).upper() == "CANCELLED":
            continue
        title = str(ev.get("SUMMARY", "")).strip()
        if not title or any(s in title.upper() for s in SKIP):
            continue

        start = ev.decoded("DTSTART")
        end = ev.decoded("DTEND") if "DTEND" in ev else None

        if isinstance(start, datetime):
            all_day = "false"
            dtstart = fmt(start)
            dtend = fmt(end) if end else dtstart
        else:  # all-day: DTEND is exclusive, so back up one day
            all_day = "true"
            last = (end - timedelta(days=1)) if end else start
            dtstart = start.strftime("%Y%m%d") + "T000000"
            dtend = last.strftime("%Y%m%d") + "T235959"

        key = (dtstart, title)          # same event on two calendars
        if key in seen:
            continue
        seen.add(key)

        out.append({
            "category": "Music & Film & Stage",
            "more_info_url": "https://www.shepherd.edu/music/calendar-of-concerts",
            "summary": title,
            "description": str(ev.get("DESCRIPTION", "")).strip(),
            "location": pick_location(str(ev.get("LOCATION", "")).strip(), title, calname),
            "dtstart": dtstart,
            "dtend": dtend,
            "allday": all_day,
        })
    return out


def escape_ics(text):
    if not text:
        return ""
    return (text.replace("\\", "\\\\").replace(",", "\\,")
                .replace(";", "\\;").replace("\r\n", "\\n").replace("\n", "\\n"))


def fold(line):
    """RFC 5545: lines over 75 octets are continued with CRLF + space."""
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line + "\r\n"
    parts, limit = [], 75
    while b:
        cut = min(limit, len(b))
        while cut < len(b) and (b[cut] & 0xC0) == 0x80:   # don't split a UTF-8 char
            cut -= 1
        parts.append(b[:cut].decode("utf-8"))
        b, limit = b[cut:], 74
    return "\r\n ".join(parts) + "\r\n"


def create_ics_file(events, filename):
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    with open(filename, "w", encoding="utf-8", newline="") as f:
        w = lambda s: f.write(fold(s))
        w("BEGIN:VCALENDAR")
        w("VERSION:2.0")
        w("PRODID:-//www.shepherd.edu/music//EN")
        w("CALSCALE:GREGORIAN")
        w("METHOD:PUBLISH")
        w("X-WR-CALNAME:Shepherd University School of Music Calendar")
        w("X-WR-TIMEZONE:America/New_York")
        for e in sorted(events, key=lambda e: e["dtstart"]):
            uid = f"{e['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, e['summary'])}@sum"
            w("BEGIN:VEVENT")
            w(f"UID:{uid}")
            w(f"DTSTAMP:{dtstamp}")
            w(f"DTSTART:{e['dtstart']}")
            w(f"DTEND:{e['dtend']}")
            w(f"SUMMARY:{escape_ics(e['summary'])}")
            w(f"LOCATION:{escape_ics(e['location'])}")
            w(f"DESCRIPTION:{escape_ics(e['description'])}")
            w(f"CATEGORIES:{e['category']}")
            w("ORGANIZATION:Shepherd University School of Music")
            w(f"URL:{e['more_info_url']}")
            w("STATUS:CONFIRMED")
            w("SOURCE:shepherd.edu/music")
            w("SEQUENCE:0")
            w("END:VEVENT")
        w("END:VCALENDAR")


def main():
    print("Shepherd University School of Music Event Extractor")
    seen, events = set(), []
    for cal_id in CALENDAR_IDS:
        try:
            cal = fetch_calendar(cal_id)
        except Exception as ex:
            print(f"  ! {cal_id}: {ex}")
            continue
        found = extract_events(cal, seen)
        print(f"  {cal.get('X-WR-CALNAME', cal_id)}: {len(found)} events")
        events.extend(found)

    if not events:
        print("\nNo events found.")
        return
    output_file = f"sum_{today_formatted}.ics"
    create_ics_file(events, output_file)
    print(f"\n✓ Saved {len(events)} events to {output_file}")


if __name__ == "__main__":
    main()