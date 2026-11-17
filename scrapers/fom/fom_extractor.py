#!/usr/bin/env python3
"""
Friends of Music Extractor with Browser Automation
This script navigates to the calendar page, clicks the List button,
and extracts all events to an ICS file.

Requirements:
    pip install selenium
    
You also need ChromeDriver installed and in your PATH
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import uuid
from datetime import datetime, timedelta
from datetime import date
import time
import re
# import sys
# import os
# # Get the absolute path of the current script's directory
# current_dir = os.path.dirname(os.path.abspath(__file__))
# # Get the path of the parent directory
# parent_dir = os.path.dirname(current_dir)
# # Insert the parent directory path into sys.path
# sys.path.insert(0, parent_dir)
import category_matcher


# Global variables
year = str(datetime.today().year)
# Format the date as a string in YYYYMMDD format
today = datetime.today()
today_formatted = today.strftime("%Y%m%d")


def setup_driver(headless=False):
    """Setup Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

def extract_date_times(date_time_string):
    dtstart = dtend = date_part = time_part = ''
    all_day = False
    start_description_with_date_time = False
    if "@" not in date_time_string:
        all_day = True
        if "-" in date_time_string:
            start_date, end_date = date_time_string.split(" - ")
            dtstart = format_date(start_date) + "T000000"
            start_description_with_date_time = True
            # dtend = format_date(end_date) + "T000000"
        else:
            start_date = format_date(date_time_string)
            dtstart = start_date + "T000000"
    else:
        date_part, time_part = date_time_string.split(" @ ")
        start_date = format_date(date_part)
        if "-" in time_part:
            begin_time, end_time = time_part.split(" - ")
            begin_time_formatted = format_time(begin_time)
            end_time_formatted = format_time(end_time)
            dtstart = start_date + "T" + begin_time_formatted + ""
            dtend = start_date + "T" + end_time_formatted + ""
        else:
            begin_time_formatted = format_time(time_part)
            dtstart = start_date + "T" + begin_time_formatted + ""

    return dtstart, dtend, all_day, start_description_with_date_time

def format_time(time):
    # time = time.replace(":", "")
    if " • " in time:
        tm, dt = time.split(" • ")
    else:
        tm, dt = time.split(",", 1)
    
    event_date = format_date(dt)
    tm=tm.replace(" ","").strip().replace("Sunday","").replace("Monday","").replace("Tuesday","").\
        replace("Wednesday","").replace("Thursday","").replace("Friday","").replace("Saturday","")
    am_pm = "pm"
    if "am" in time: am_pm = "am"
    tm = tm.replace(am_pm, "")
    hh, mm = tm.split(":")
    if am_pm == "pm" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    event_time = hh + mm + "00"
    return (event_date + "T" + event_time + ""), event_date

def format_date(date_str):
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    date_str = date_str.strip()
    if \
    ("Sunday" in date_str  or "Monday" in date_str  or "Tuesday" in date_str  or "Wednesday" in date_str  or \
    "Thursday" in date_str  or "Friday" in date_str  or "Saturday" in date_str ):        
        dow, month_day, year = date_str.split(",")
    else:
        month_day, year = date_str.split(",")
    year = year.strip()
    month_day = month_day.strip()
    month, day = month_day.split(" ")
    month = month.strip()
    match month:
        case "January": month = "01"
        case "February": month = "02"
        case "March": month = "03"
        case "April": month = "04"
        case "May": month = "05"
        case "June": month = "06"
        case "July": month = "07"
        case "August": month = "08"
        case "September": month = "09"
        case "October": month = "10"
        case "November": month = "11"
        case "December": month = "12"
    day = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', day)
    if len(day) == 1: day = "0" + day
    # print('month:', month, ' day:', day)
    return year + month + day

WEEKDAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
DATE_RE = re.compile(r"(%s)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})" % "|".join(MONTHS))
TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b", re.I)
CITY_RE = re.compile(r",\s*[A-Z]{2}$")          # "Shepherdstown, WV"
SKIP_RE = re.compile(r"^(tickets?|buy tickets|program notes|download program)$|\$\d", re.I)


def find_dates(lines):
    """Return (index_range, 'YYYYMMDDTHHMMSS') for each performance.

    Handles both layouts:
      new:  'Sunday' / 'November 15, 2026' / '3:00 pm'   (three lines)
      old:  'Sunday, November 15, 2026 • 3:00 pm'        (one line)
    """
    found = []
    for i, line in enumerate(lines):
        m = DATE_RE.search(line)
        if not m:
            continue
        # the time is on this line (old layout) or within the next 2 lines
        t, used = TIME_RE.search(line[m.end():]), {i}
        j = i
        while t is None and j < min(i + 2, len(lines) - 1):
            j += 1
            if DATE_RE.search(lines[j]):
                break
            t = TIME_RE.search(lines[j])
            used.add(j)
        if i > 0 and lines[i - 1].strip() in WEEKDAYS:
            used.add(i - 1)
        month = MONTHS.index(m[1]) + 1
        ymd = f"{m[3]}{month:02d}{int(m[2]):02d}"
        if t:
            hh, mm, ap = int(t[1]), int(t[2] or 0), t[3].lower()
            if ap == "p" and hh != 12:
                hh += 12
            if ap == "a" and hh == 12:
                hh = 0
            found.append((used, f"{ymd}T{hh:02d}{mm:02d}00"))
        else:
            found.append((used, f"{ymd}T000000"))
    return found


def extract_event_info(block_text, events_extracted):
    """Parse one concert block (its visible text) into events, one per date."""
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    if len(lines) < 2:
        return
    dates = find_dates(lines)
    if not dates:
        return
    date_lines = set().union(*(u for u, _ in dates))

    # first line = tagline, second = ensemble (same as the old summary)
    tagline, title = lines[0], lines[1]
    if lines[0].isupper() is False and len(lines[0]) > 60:  # no tagline
        tagline, title = "", lines[0]
    summary = f"{tagline} - {title}" if tagline else title

    # location: the line just above a 'City, ST' line, joined with it
    location, loc_lines = "", set()
    for i, l in enumerate(lines[2:], start=2):
        if CITY_RE.search(l) and i not in date_lines:
            location = f"{lines[i-1]}, {l}" if i - 1 >= 2 else l
            loc_lines = {i - 1, i}
            break

    body = [l for i, l in enumerate(lines[2:], start=2)
            if i not in date_lines and i not in loc_lines and not SKIP_RE.search(l)
            and l not in WEEKDAYS]
    description = "\n".join(body)

    for _, dtstart in dates:
        if dtstart[:8] >= today_formatted:
            events_extracted.append({
                'category': 'Music & Film & Stage',
                'time': '',
                'more_info_url': 'https://www.friendswv.org/2026-2027-season/',
                'more_info_text': '',
                'summary': summary,
                'description': description,
                'location': location,
                'location_details': '',
                'contact_name': '',
                'contact_phone': '',
                'contact_email': '',
                'dtstart': dtstart,
                'dtend': '',
                'allday': ''
            })


def concert_blocks(driver):
    """Find each concert's container without relying on theme class names:
    start at every <h2> and climb to the largest ancestor that still holds
    only that one <h2>."""
    js = """
    const out = [];
    for (const h of document.querySelectorAll('h2')) {
      let el = h;
      while (el.parentElement && el.parentElement !== document.body &&
             el.parentElement.querySelectorAll('h2').length === 1) {
        el = el.parentElement;
      }
      out.push(el.innerText);
    }
    return out;
    """
    return driver.execute_script(js)


def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//www.friendswv.org/EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Friends of Music Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@fom"
            
            # Format dates
            dtstamp = datetime.now().strftime('%Y%m%dT%H%M%S')
            dtstart = event['dtstart']
            dtend = event['dtend']
            
            # Escape special characters
            def escape_ics(text):
                if not text:
                    return ""
                return (text.replace('\\', '\\\\')
                           .replace(',', '\\,')
                           .replace(';', '\\;')
                           .replace('\n', '\\n'))
            
            summary = escape_ics(event['summary'])
            # location = escape_ics(event['location'])
            location = event['location']
            description = escape_ics(event['description'])
            # category = ', '.join(event['category'])
            category = event['category']
            url = event.get('more_info_url', '')
            
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"LOCATION:{location}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"CATEGORIES:{category}\n")
            f.write(f"ORGANIZATION:Friends of Music\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:friendswv.org/\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    # print("="*70)
    print("Friends of Music Calendar Event Extractor")
    # print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        # print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=True)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://www.friendswv.org/2026-2027-season"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        # print("Waiting for page to load...")
        time.sleep(3)
        
        events_extracted = []
        # pages_scraped = 0

        # Extract up to a maximum months. Keep 1 or 2 while testing
        # max_pages = 5
        # while pages_scraped < max_pages:
            # pages_scraped += 1
        blocks = concert_blocks(driver)
        print(f"Found {len(blocks)} headings")
        for block_text in blocks:
            extract_event_info(block_text, events_extracted)
            # if event_elements['summary'] != "":
            #     events_extracted.append(event_elements)
                # break

            # Click next month button
            # if pages_scraped < max_pages:
            #     click_next_month_button(driver, wait)
            #     time.sleep(5)
            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'fom_' + today_formatted + '.ics'
            print(f"\nSaving {len(events_extracted)} events to {output_file}...")
            create_ics_file(events_extracted, output_file)
            print(f"✓ ICS file created successfully!")
            
            # Print summary
            # print("\n" + "="*70)
            # # print("EVENTS SUMMARY")
            # # print("="*70)
            # for i, event in enumerate(events_extracted[:5], 1):
            #     print(f"\n{i}. {event['summary']}")
            #     print(f"   Date: {event['dtstart']}")
            #     print(f"   Location: {event['location']}")
            
            # if len(events_extracted) > 5:
            #     print(f"\n... and {len(events_extracted) - 5} more events")
            
            # print("\n" + "="*70)
            print(f"Total events: {len(events_extracted)}")
            # print("="*70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
            # print("Done!")

if __name__ == "__main__":
    main()