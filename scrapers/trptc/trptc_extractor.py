#!/usr/bin/env python3
"""
The Roving Peregrine Theatre Company Extractor with Browser Automation
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
            # dtend = format_date(end_date) + "T000000Z"
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
    # time = time.replace(":", "")
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
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    date_str = date_str.strip()
    dow, month, day = date_str.split(" ")
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

def extract_event_info(event_elements):
    """
    Extract Category, More Info, Description, Location, Contact, Phone, and Email
    from event text string
    """
    # print('event_elements:', event_elements.text)
    # print(126, heading)
    # for char in heading:
    #     print('char:', char, ' code:', ord(char))

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
        h1_element = event_elements.find_element(By.TAG_NAME, "h1")
        anchor_element = h1_element.find_element(By.TAG_NAME, "a")
        title = h1_element.text
        category = []
        category = category_matcher.categorize_by_keywords(title)
        href = anchor_element.get_attribute("href")
        # print(title, href)
        event_times = event_elements.find_elements(By.CLASS_NAME, "event-time-localized")
        for event_time in event_times:
            dt = event_time.get_attribute("datetime")
            dtstart = dt.replace("-","") + "T" + format_time(event_time.text) + "Z"
            # print('dt:', dt, ' event_time:', event_time.text, ' dtstart:', dtstart)
        location = "The Black Box Arts Center - 113 South Princess Street, Shepherdstown"
        organization = "The Roving Peregrine Theatre Company"
        result['category'] = category
        result['more_info_url'] = href
        result['summary'] =  title
        result['organization'] = organization
        result['location'] = location
        result['dtstart'] = dtstart
        return result
        # title_link = event_elements.find_element(By.CLASS_NAME, "eventlist-title-link")
    except:
        return result    

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//rovingperegrinetheatre.org//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:The Roving Peregrine Theatre Company Events\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@trptc"
            
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
            # category = escape_ics(event['category'])
            if len(event['category']) > 0:
                category = ', '.join(event['category'])
            else:
                category = 'Film & Performing Arts'
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
            f.write(f"ORGANIZATION:The Roving Peregrine Theatre Company\n")           
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:rovingperegrinetheatre.org\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    print("="*70)
    print("The Roving Peregrine Theatre Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://www.rovingperegrinetheatre.org/shows"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 50)
        print("Waiting for page to load...")
        time.sleep(5)
        
        events_extracted = []
        # pages_scraped = 0

        # Extract up to a maximum months. Keep 1 or 2 while testing
        # max_pages = 5
        # while pages_scraped < max_pages:
            # pages_scraped += 1

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:

            # Scroll down to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load (adjust wait time as needed)
            time.sleep(5)

            # Calculate new page height and compare with the last height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same, you have reached the end
                break
            last_height = new_height

        events = driver.find_elements(By.CSS_SELECTOR, ".eventlist-column-info")
        for event in events:
            try:
                event_elements = extract_event_info(event)
                # continue
            except Exception as e:
                print(f"\nError: {e}")
                continue

            if event_elements['summary'] != "":
                events_extracted.append(event_elements)
                # break

        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'trptc_' + today_formatted + '.ics'
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
