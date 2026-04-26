#!/usr/bin/env python3
"""
Shepherdstown Mystery Walks\ Calendar Event Extractor with Browser Automation
This script navigates to the calendar page, clicks the List button,
and extracts all events to an ICS file.

Requirements:
    pip install selenium
    
You also need ChromeDriver installed and in your PATH
"""

# import sys
# import os
# # Get the absolute path of the current script's directory
# current_dir = os.path.dirname(os.path.abspath(__file__))
# # Get the path of the parent directory
# parent_dir = os.path.dirname(current_dir)
# # Insert the parent directory path into sys.path
# sys.path.insert(0, parent_dir)

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
# import category_matcher

# Global variables
year = "2026"
global_month = ""
day = "01"
# Format the date as a string in YYYYMMDD format
today = datetime.today()
today_formatted = today.strftime("%Y%m%d")
description = "Duration 1 hour and 30 minutes\n" + \
    "Stroll through Shepherdstown with a costumed guide who leads you by candlelight from one haunted and historic location to the next.\n\n" + \
    "Easy 1 mile Walk. Dog-friendly!"


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
    time=time.replace(" ","")
    am_pm = "PM"
    if "AM" in time: am_pm = "AM"
    time = time.replace(am_pm, "")
    hh, mm = time.split(":")
    if am_pm == "PM" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    return (hh + mm + "00")

def extract_event_info(line, events_extracted):
    """
    Extract Category, More Info, Description, Location, Contact, Phone, and Email
    from event text string
    """
    # result = {
    #     'category': '',
    #     'time': '',
    #     'more_info_url': '',
    #     'more_info_text': '',
    #     'summary': '',
    #     'description': '',
    #     'location': '',
    #     'location_details': '',
    #     'contact_name': '',
    #     'contact_phone': '',
    #     'contact_email': '',
    #     'dtstart': '',
    #     'dtend': '',
    #     'allday': ''
    # }
    global global_month
    global day
    global year
    global description
    if line > '':
        # print(197, line)
        if line.startswith("Jan"): 
            global_month = "01"
            day = "01"
            # return
        if line.startswith("Feb"): 
            print("FEBRUARY")
            global_month = "02"
            day = "01"
            # print('global_month:', global_month)
            # return
        if line.startswith("Mar"): 
            global_month = "03"
            day = "01"
            # return
        if line.startswith("Apr"): 
            global_month = "04"
            day = "01"
            # return
        if line.startswith("May"): 
            global_month = "05"
            day = "01"
            # return
        if line.startswith("Jun"): 
            global_month = "06"
            day = "01"
            # return
        if line.startswith("Jul"): 
            global_month = "07"
            day = "01"
            # return
        if line.startswith("Aug"): 
            global_month = "08"
            day = "01"
            # return
        if line.startswith("Sep"): 
            global_month = "09"
            day = "01"
            # return
        if line.startswith("Oct"): 
            global_month = "10"
            day = "01"
            # return
        if line.startswith("Nov"): 
            global_month = "11"
            day = "01"
            # return
        if line.startswith("Dec"): 
            global_month = "12"
            day = "01"
            # return
        # print('249 global_month:', global_month)

        if "Ghost Tour" in line:
            # print('252 global_month:', global_month)
            tm, event = line.split(" Ghost Tour")
            time = format_time(tm)
            dtstart = year + global_month + day + "T" + time + "Z"
            result = {
                'category': 'History',
                'time': '',
                'more_info_url': 'https://shepherdstownmysterywalks.com/',
                'more_info_text': '',
                'summary': 'Ghost Tour!',
                'description': description,
                'location': 'Welcome Center at the Market House, 100 East German St, Shepherdstown',
                'location_details': '',
                'contact_name': 'Janet Hughes',
                'contact_phone': '(301) 639-0351',
                'contact_email': 'jhughes@shepherdstownmysterywalks.com',
                'dtstart': dtstart,
                'dtend': '',
                'allday': ''
            }
            events_extracted.append(result)
            # return
            # continue
        if line.isnumeric():
            if len(line) == 1: day = "0" + line
            else: day = line
        # print('275 global_month:', global_month)

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//potomacaudubon.org//calendar//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherdstown Mystery Walks Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@ghost"
            
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
            # category = ', '.join(event['category'])
            category = event['category']
            url = event.get('more_info_url', '')
            # address = ''
            # print('dtstart:', dtstart)
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"LOCATION:{location}\n")
            # f.write(f"ADDRESS:{address}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"CATEGORIES:{category}\n")
            f.write(f"ORGANIZATION:Shepherdstown Mystery Walks\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:shepherdstownmysterywalks.com/\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    print("="*70)
    print("Shepherdstown Mystery Walks Calendar Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://fareharbor.com/embeds/book/shepherdstownmysterywalks/items/190345/calendar/"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        print("Waiting for page to load...")
        time.sleep(5)
        
        events_extracted = []
        pages_scraped = 0
        events = driver.find_elements(By.CLASS_NAME, "month-current")

        # Extract up to a maximum months. Keep 1 or 2 while testing
        max_pages = 3
        while pages_scraped < max_pages:
            # pages_scraped += 1
            print("scraping ", pages_scraped)
            events = driver.find_elements(By.CLASS_NAME, "month-current")
            for event in events:
                # print('pages_scraped:', pages_scraped)
                # print(event.text)
                event_lines = event.text.strip().split("\n")
                for line in event_lines:
                    extract_event_info(line, events_extracted)
                # if event_elements['dtstart'] > '':
                #     events_extracted.append(event_elements)
                # break
            pages_scraped += 1

            # Click next month button
            if pages_scraped < max_pages:
                try:
                    button = driver.find_element(By.CLASS_NAME, "test-select-next-month-action")
                    button.click()
                    wait = WebDriverWait(driver, 10)
                    print("Waiting for page to load...")
                    time.sleep(5)
                    print("✓ Clicked Next Month button")
                except Exception as e:
                    print(f"\nError: {e}")
                    import traceback
                    traceback.print_exc()

                
                # url = "https://fareharbor.com/embeds/book/shepherdstownmysterywalks/items/190345/calendar/2026/03/?full-items=yes" + str(pages_scraped) + "/"
                # print(url)
                # print(f"Navigating to {url}")
                # driver.get(url)                
                # # Wait for page to load
                # wait = WebDriverWait(driver, 50)
                # print("Waiting for page to load...")
                #     time.sleep(5)
                 
                
                # cont = click_next_month_button(driver)
                # if not cont:
                #     max_pages = pages_scraped
            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'ghost_' + today_formatted + '.ics'
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
