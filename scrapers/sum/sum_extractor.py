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
year = "2026"
# Format the date as a string in YYYYMMDD format
today = datetime.today()
last_date = today + timedelta(days=120)
today_formatted = today.strftime("%Y%m%d")
last_date_formatted = last_date.strftime("%Y%m%d")


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

def format_time(time):
    # time = time.replace(":", "")
    # print('time:', time, " – " in time)
    # for character in time:
    #     # Use ord() to get the character code and print it
    #     print(f"Character: '{character}' | Code: {ord(character)}")
    # time = time.replace(chr(32), "")
    # print("time:", time)
    if " – " in time:
        start, end = time.split(" – ")
    else:
        start = time
        end = ""
    # print('start:', start, 'end:', end)
    time=time.replace(" ","").strip()
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
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    # print(130, date_str)
    if "today" in date_str:
        date_str = date_str.replace(", today","")
    date_str = date_str.strip()
    dow, month_day = date_str.split(", ")
    month, day = month_day.split(" ")
    # print(134, month_day, month, day)
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

# def create_dtstart(date_element, dd):
#     # print('date_element:', date_element, 'dd:', dd)
#     date = format_date(date_element)
#     tm =format_time(dd)
#     return date + "T" + tm + "Z"

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
            dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
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
            
            # summary = escape_ics(event['summary'])
            summary = event['summary']
            # location = escape_ics(event['location'])
            location = event['location']
            description = escape_ics(event['description'])
            # category = escape_ics(event['category'])
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
    print("="*70)
    print("Shepherdstown University School of Music Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
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
            # "&color=%2333B679&color=%237CB342&color=%23F09300&color=%234285F4&color=%23c53f00&color=%23F4511E&color=%234285F4&color=%23EF6C00&color=%23AD1457" + \
            # "&color=%23B39DDB&color=%23F6BF26&color=%23C0CA33&&mode=AGENDA"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 200)
        print("Waiting for page to load...")
        time.sleep(10)
        
        events_extracted = []
        events = driver.find_elements(By.CLASS_NAME, "YOmXMd")
        # print(283, len(events))
        event_date = ''
        for event in events:
            times = ''
            start_time = ''
            end_time = ''
            location = ''
            title = ''
            desc = ''
            all_day = 'false'
            try:
                event_date = event.find_element(By.CLASS_NAME,"V4sZ3c").find_element(By.CLASS_NAME,"bf2t7b").find_element(By.CLASS_NAME,"H3yh2e").get_attribute("aria-label")
                # print('event_date:', event_date)
                event_date = format_date(event_date)
                # print(311, event.text, event_date)
            except:
                pass
            # print(event_date, last_date_formatted)

            if event_date > last_date_formatted: # (today + timedelta(days=90).strftime("%Y%m%d")):
                break
            # print('event_date:', event_date.get_attribute("aria-label"))
            # presentation = event.find_element()
            lines = event.text.split('\n')
            # print('')
            # for line in lines:
            # for index, line in enumerate(lines):
            #     print('line:', index, line, line.isnumeric())
            if len(lines) < 3:
                print('skipping')
            else:
                if lines[0].isnumeric(): start_line = 2
                else: 
                    start_line = 1
                # print('start_line:', start_line)
                times = lines[start_line]
                title = lines[start_line + 1]
                try:
                    location = lines[start_line + 2]
                except:
                    location = "Shepherd University"
            # Skip certain conditions
            if "Ram Pep Band" not in title and "Ram Band Camp" not in title and "String Camp" not in title and \
                "Home Football Game" not in title:

                if times == "All day":
                    all_day = 'true'
                    dtstart = event_date + "T" + "000000Z"
                    dtend = event_date + "T" + "235959Z"
                else:
                    if times == '' and title == '':
                        continue
                    else:
                        start_time, end_time = format_time(times)
                        dtstart = event_date + "T" + start_time + "Z"
                        dtend = event_date + "T" + end_time + "Z"
                # print('times:', times, 'start_time:', start_time, 'dtstart:', dtstart)
                
                # # Skip certain conditions
                # if "Ram Pep Band" not in title and "Ram Band Camp" not in title:

                # print('event_date:', event_date, 'start_time:', start_time, 'dtstart:', dtstart, 'dtend:', dtend, 'end_time:', end_time, 'all_day:', all_day, 'location:', location, 'title:', title, 'desc:', desc)
                
                result = {
                    'category': "Film & Performing Arts",
                    'time': '',
                    'more_info_url': 'https://www.shepherd.edu/music/calendar-of-concerts',
                    'more_info_text': '',
                    'summary': title,
                    'description': desc,
                    'location': location,
                    'location_details': '',
                    'contact_name': '',
                    'contact_phone': '',
                    'contact_email': '',
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'allday': all_day
                }
                
                events_extracted.append(result)


        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'sum_' + today_formatted + '.ics'
            print(f"\nSaving {len(events)} events to {output_file}...")
            create_ics_file(events_extracted, output_file)
            print(f"✓ ICS file created successfully!")
            
            # Print summary
            print("\n" + "="*70)
            print("EVENTS SUMMARY")
            print("="*70)
            for i, event in enumerate(events_extracted[:5], 1):
                print(f"\n{i}. {event['summary']}")
                print(f"   Date: {event['dtstart']}")
                print(f"   Location: {event['location']}")
            
            if len(events_extracted) > 5:
                print(f"\n... and {len(events_extracted) - 5} more events")
            
            print("\n" + "="*70)
            print(f"Total events: {len(events_extracted)}")
            print("="*70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()
            print("Done!")

if __name__ == "__main__":
    main()
