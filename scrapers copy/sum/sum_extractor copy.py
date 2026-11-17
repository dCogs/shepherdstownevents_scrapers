#!/usr/bin/env python3
"""
Shepherdstown University School of Music Extractor with Browser Automation
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
# import category_matcher


# Global variables
year = str(datetime.today().year)
# Format the date as a string in YYYYMMDD format
today = datetime.today()
last_date = today + timedelta(days=180)
today_formatted = today.strftime("%Y%m%d")
last_date_formatted = last_date.strftime("%Y%m%d")

# A line like "9 – 11am", "7:30 – 8:30pm", "7pm"
TIME_RE = re.compile(r'^\d{1,2}(:\d{2})?\s*(am|pm)?(\s*[–-]\s*\d{1,2}(:\d{2})?\s*(am|pm))?$')
FRANK = "Frank Arts Center 260 University Dr, Shepherdstown, WV 25443"
SKIP = ["RAM PEP BAND", "RAM BAND CAMP", "STRING CAMP", "HOME FOOTBALL GAME",
        "RB EXHIBITION", "SUMMER CLINIC", "REHEARSAL", "RAM BAND TOUR"]


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


def is_time_line(line):
    line = line.strip()
    if line == "All day":
        return True
    # require am/pm so the bare day number ("5") isn't mistaken for a time
    return bool(TIME_RE.match(line)) and ("am" in line or "pm" in line)


def default_location(title):
    t = title.lower()
    if "parade" in t:
        return "Shepherdstown"
    return FRANK if "salon series" in t else "Shepherd University"


def parse_event_lines(lines):
    """Return (times, title, location) for every event in a block of text.
    A time line starts a new event; the next line is the title; the line
    after that is the location only if it isn't another time line."""
    parsed = []
    i = 0
    while i < len(lines):
        if not is_time_line(lines[i]):
            i += 1                      # skips "5", "Dec, Sat", stray lines
            continue
        times = lines[i].strip()
        title = lines[i + 1].strip() if i + 1 < len(lines) else ''
        location = ''
        j = i + 2
        if j < len(lines) and not is_time_line(lines[j]):
            location = lines[j].strip()
            j += 1
        if not location:
            location = default_location(title)
        elif location.startswith("Calendar:"):
            # No venue given: concerts default to Frank, marching band events don't
            if "marching band" in location.lower():
                location = default_location(title)
            else:
                location = FRANK
        parsed.append((times, title, location))
        i = j
    return parsed


def format_time(time):
    if " – " in time:
        start, end = time.split(" – ")
    else:
        start = time
        end = ""
    am_pm = "pm"
    if "am" in end: am_pm = "am"
    if "am" not in start and "pm" not in start:
        start += am_pm
    start_time = convert_time(start)
    if end != "":
        end_time = convert_time(end)
    else:
        end_time = ""
    return start_time, end_time


def convert_time(time):
    am_pm = "pm"
    if "am" in time: am_pm = "am"
    time = time.replace(am_pm, "")
    if ":" in time:
        hh, mm = time.split(":")
    else:
        hh = time
        mm = "00"
    if am_pm == "pm" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    return (hh + mm.strip() + "00")


def format_date(date_str):
    if "today" in date_str:
        date_str = date_str.replace(", today","")
    date_str = date_str.strip()
    dow, month_day = date_str.split(", ")
    month, day = month_day.split(" ")
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
    return year + month + day


def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//www.shepherd.edu/music//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherd University School of Music Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@sum"
            
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
            
            summary = event['summary']
            location = event['location']
            description = escape_ics(event['description'])
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
            f.write(f"ORGANIZATION:Shepherd University School of Music\n")           
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:shepherd.edu/music\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")


def main():
    """Main function"""
    print("Shepherdstown University School of Music Event Extractor")
    print()
    
    driver = None
    try:
        driver = setup_driver(headless=True)  # Set to True to run in background

        # Navigate to calendar page
        url = "https://www.shepherd.edu/music/calendar-of-concerts"
        url = "https://calendar.google.com/calendar/u/0/embed?height=600&wkst=1&ctz=America/New_York&bgcolor=%23ffffff&showPrint=0" + \
            "&title=School+of+Music+Events&src=czFzamphYTBsYmdqa2tmODdtYW5icnBhNzRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&src=ZG1uYzFhamtiYzJkbDk4YjNtYWd0b244MWtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&src=bjNrdmxnMzJzODRjNHVnOHNyczVscjFscThAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&src=OGt0YmZuNDQwMTJrNHVwMTJ0aG80dmRpa2tAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&src=aGllcDd1YmdjZ3I4ZDZnbmNuNTdqc3RiZW9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&src=MXQzMmtnZmhyZjkyZmUwZ2RkN3NyOXJ1ZDRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&" \
            "src=Zm9wMzJkY3FwcWRjMHFmaGZobHQxN291MjBAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&src=YzMwMjdsdHFqY2J1azFwYWs4dGljamdkZW9AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&src=c2J2ZDMzaHZiN3ZrZWR1NDE5YXRya2hndWtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&src=c2I5NzFyNWRucWpkdDBuZjZjOGs2MWJkYjRAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&src=N2NvZnU2OGFmN2I0aG8xNjQzZjFhY3FidThAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ&src=aWhnaHMycXNtNWQwbjRxM3NrdWZpN2xtZ29AZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ" + \
            "&mode=AGENDA"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 200)
        time.sleep(10)
        
        events_extracted = []
        seen = set()
        events = driver.find_elements(By.CLASS_NAME, "YOmXMd")
        event_date = ''
        for event in events:
            try:
                event_date = event.find_element(By.CLASS_NAME,"V4sZ3c").\
                    find_element(By.CLASS_NAME,"bf2t7b").\
                    find_element(By.CLASS_NAME,"H3yh2e").\
                    get_attribute("aria-label")
                event_date = format_date(event_date)
            except:
                pass  # no date header on this row; keep the previous date

            if event_date > last_date_formatted:
                break

            lines = event.text.split('\n')
            # print('')
            # for index, line in enumerate(lines):
            #     print('line:', index, line)

            for times, title, location in parse_event_lines(lines):
                if not title or any(s in title.upper() for s in SKIP):
                    continue
                # print('title:', title, '| location:', location)

                if times == "All day":
                    all_day = 'true'
                    dtstart = event_date + "T000000"
                    dtend = event_date + "T235959"
                else:
                    all_day = 'false'
                    start_time, end_time = format_time(times)
                    dtstart = event_date + "T" + start_time
                    dtend = event_date + "T" + end_time

                # guards against a day block and its child rows both matching YOmXMd
                key = (dtstart, title)
                if key in seen:
                    continue
                seen.add(key)

                events_extracted.append({
                    'category': "Music & Film & Stage",
                    'time': '',
                    'more_info_url': 'https://www.shepherd.edu/music/calendar-of-concerts',
                    'more_info_text': '',
                    'summary': title,
                    'description': '',
                    'location': location,
                    'location_details': '',
                    'contact_name': '',
                    'contact_phone': '',
                    'contact_email': '',
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'allday': all_day
                })

        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            output_file = 'sum_' + today_formatted + '.ics'
            print(f"\nSaving {len(events_extracted)} events to {output_file}...")
            create_ics_file(events_extracted, output_file)
            print(f"✓ ICS file created successfully!")
            print(f"Total events: {len(events_extracted)}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()


if __name__ == "__main__":
    main()