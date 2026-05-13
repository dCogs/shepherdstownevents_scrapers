#!/usr/bin/env python3
"""
Four Seasons Books Extractor with Browser Automation
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
year = "2026"
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
            dtstart = format_date(start_date) + "T000000Z"
            start_description_with_date_time = True
        else:
            start_date = format_date(date_time_string)
            dtstart = start_date + "T000000Z"
    else:
        date_part, time_part = date_time_string.split(" @ ")
        start_date = format_date(date_part)
        if "-" in time_part:
            begin_time, end_time = time_part.split(" - ")
            begin_time_formatted = format_time(begin_time)
            end_time_formatted = format_time(end_time)
            dtstart = start_date + "T" + begin_time_formatted + "Z"
            dtend = start_date + "T" + end_time_formatted + "Z"
        else:
            begin_time_formatted = format_time(time_part)
            dtstart = start_date + "T" + begin_time_formatted + "Z"

    return dtstart, dtend, all_day, start_description_with_date_time

def format_time(time):
    time=time.replace(" ","").strip()
    am_pm = "PM"
    if "AM" in time: am_pm = "AM"
    time = time.replace(am_pm, "")
    hh, mm = time.split(":")
    if am_pm == "PM" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    return (hh + mm.strip() + "00")


def format_date(date_str):
    date_str = date_str.strip()
    month, day = date_str.split(" ")
    match month:
        case "Jan": month = "01"
        case "Feb": month = "02"
        case "Mar": month = "03"
        case "Apr": month = "04"
        case "May": month = "05"
        case "Jun": month = "06"
        case "Jul": month = "07"
        case "Aug": month = "08"
        case "Sep": month = "09"
        case "Oct": month = "10"
        case "Nov": month = "11"
        case "Dec": month = "12"
    day = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', day)
    if len(day) == 1: day = "0" + day
    # print('month:', month, ' day:', day)
    return year + month + day

def extract_event_info(event_elements):
    """
    Extract Category, More Info, Description, Location, Contact, Phone, and Email
    from event text string
    """
    result = {
        'category': '',
        'time': '',
        'more_info_url': '',
        'more_info_text': '',
        'summary': '',
        'description': '',
        'location': '',
        'location_details': '',
        'contact_name': '',
        'contact_phone': '',
        'contact_email': '',
        'dtstart': '',
        'dtend': '',
        'allday': ''
    }
    try:
        event_card_link = event_elements.find_element(By.CLASS_NAME, "event-card-link")
        title_href = event_card_link.get_attribute("href")
        event_details = event_elements.find_element(By.CLASS_NAME, "event-card-details")
        all_descendant_tags = event_details.find_elements(By.CLASS_NAME, "Typography_root__487rx")
        title = ''
        event_date = ''
        location = ''
        for element in all_descendant_tags:
            element_text = element.get_attribute('textContent')
            if title == '': 
                title = element_text
            else:
                if event_date == '':
                    event_date = element_text
                    dt, tm = event_date.split(" • ")
                    #remove day of week
                    day, mon_day = dt.split(", ")
                    dt = format_date(mon_day)
                    # Don't post expired events
                    if dt < today_formatted:
                        return result
                    tm = format_time(tm)
                    dtstart = dt + "T" + tm + "Z"
                else:
                    if location == '':
                        location = element_text
        category = []
        category = category_matcher.categorize_by_keywords(title)

    except:
        return result    
    
    result['more_info_url'] = title_href
    result['more_info_text'] = title
    result['summary'] = title
    result['description'] = ''
    result['location'] = location
    result['dtstart'] = dtstart
    result['dtend'] = ''  
    result['category'] = category
    # print("result:", result)
    return result

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//fourseasonsbooks.com/events//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Four Seasons Books Events Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@4seasons"
            
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
            
            summary = escape_ics(event['summary'])
            # location = escape_ics(event['location'])
            location = event['location']
            description = escape_ics(event['description'])
            if len(event['category']) > 0:
                category = ', '.join(event['category'])
            else:
                category = 'Arts & Culture'
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
            f.write(f"ORGANIZATION:Four Seasons Books\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:https://www.fourseasonsbooks.com\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    # print("="*70)
    print("Four Seasons Calendar Event Extractor")
    # print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        # print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=True)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://www.eventbrite.com/o/four-seasons-books-69316370703"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        # # print("Waiting for page to load...")
        time.sleep(5)
        
        events_extracted = []
        current_events = driver.find_element(By.CSS_SELECTOR, "[data-testid='organizer-profile__future-events']")
        element = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "Typography_root__487rx"))
        )
        events = current_events.find_elements(By.CSS_SELECTOR, ".event-card__vertical")

        # Loop through current events
        for event in events:
            event_elements = extract_event_info(event)
            if event_elements['summary'] != "":
                events_extracted.append(event_elements)
            # break
            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = '4seasons_' + today_formatted + '.ics'
            print(f"\nSaving {len(events_extracted)} events to {output_file}...")
            create_ics_file(events_extracted, output_file)
            print(f"✓ ICS file created successfully!")
            
            # Print summary
            # print("\n" + "="*70)
            # # print("EVENTS SUMMARY")
            # print("="*70)
            for i, event in enumerate(events_extracted[:5], 1):
                print(f"\n{i}. {event['summary']}")
                print(f"   Date: {event['dtstart']}")
                print(f"   Location: {event['location']}")
            
            if len(events_extracted) > 5:
                print(f"\n... and {len(events_extracted) - 5} more events")
            
            print("\n" + "="*70)
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
