#!/usr/bin/env python3
"""
Antietam National Battlefield Extractor with Browser Automation
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
            dtstart = format_date_time(start_date) + "T000000Z"
            start_description_with_date_time = True
            # dtend = format_date_time(end_date) + "T000000Z"
        else:
            start_date = format_date_time(date_time_string)
            dtstart = start_date + "T000000Z"
    else:
        date_part, time_part = date_time_string.split(" @ ")
        start_date = format_date_time(date_part)
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
    am_pm = "pm"
    if "am" in time: am_pm = "am"
    time = time.replace(am_pm, "")
    hh, mm = time.split(":")
    if am_pm == "pm" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    return (hh + mm.strip() + "00")


def format_date_time(date_str):
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    date_str = date_str.strip()
    dow,dt_tm = date_str.split(", ")
    dt, tm = dt_tm.split(" • ")
    # print(101, date_str)
    month, day = dt.split(" ")
    # print(106, month, day)
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
    if len(day) == 1: day = "0" + day
    time = format_time(tm)
    # print('month:', month, ' day:', day, ' time:', time)
    return year + month + day + "T" + time + "Z"

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
        # print(153, event_elements.text)
        # if heading.count('\n') == 2:
        #     title, dt, tm = heading.split('\n')
        # if heading.count('\n') == 3:
        #     title, dt, tm, dummy = heading.split('\n')
        # print(154, dt)
        # date_YMD = format_date_time(dt)
        # print(156, date_YMD)
        # time_HMS = format_time(tm)
        # dtstart = date_YMD + "T" + time_HMS + "Z"
        # print('dtstart:', dtstart)
        # print('title:', title, ' dt:', dt, ' tm:', tm)
        tag = event_elements.find_element(By.CLASS_NAME,'usa-card__tag-list').text
        # print('tag:', tag)
        if "Special Event" not in tag: return result

        link = event_elements.find_element(By.CLASS_NAME,'usa-card__link')
        # title = link.text
        more_info_url = link.get_attribute("href")
        title = event_elements.find_element(By.CLASS_NAME,'usa-card__header').\
            find_element(By.TAG_NAME,'h1').text
        # print('title:', title)
        # print('link:', more_info_url)
        date_string = event_elements.find_element(By.CLASS_NAME,'usa-card__header').\
            find_element(By.CLASS_NAME,'usa-card__subheading').text
        # print('date_string:', date_string)
        dtstart = format_date_time(date_string)
        # print('dtstart:', dtstart)
        category = ['History']
        # para = event_elements.find_element(By.TAG_NAME, 'p').text
        # newline_index = para.find('\n')
        location = "Antietam National Battlefield, 5831 Dunker Church Rd, Sharpsburg"
        # print('location:', location)
        result['category'] = category
        result['more_info_url'] = more_info_url
        result['summary'] = title
        result['location'] = location
        result['dtstart'] = dtstart
        # print('result:', result)
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
        f.write("PRODID:-//speakstoryseries.com//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Antietam National Battlefield Events\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@anb"
            
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
            # description = escape_ics(event['description'])
            # category = escape_ics(event['category'])
            if len(event['category']) > 0:
                category = ', '.join(event['category'])
            else:
                category = 'Music & Film & Stage'

            url = event.get('more_info_url', '')
            
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"LOCATION:{location}\n")
            # f.write(f"DESCRIPTION:{''}\n")
            f.write(f"CATEGORIES:{category}\n")
            f.write(f"ORGANIZATION:Antietam National Battlefield\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:www.nps.gov/anti\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    # print("="*70)
    print("Antietam National Battlefield Event Extractor")
    # # print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        # print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://www.nps.gov/anti/planyourvisit/calendar.htm"
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
        events = driver.find_elements(By.CSS_SELECTOR, ".usa-card__container")
        for event in events:
            try:
                # print(event.text)
                # heading = event.find_element(By.TAG_NAME, "h1").text
                # print(heading)
                # if heading.startswith("Pluribus:"): continue
                event_elements = extract_event_info(event)
                # continue
            except Exception as e:
                # print(f"\nError: {e}")
                continue

            if event_elements['summary'] != "":
                events_extracted.append(event_elements)
                # break

            # Click next month button
            # if pages_scraped < max_pages:
            #     click_next_month_button(driver, wait)
            #     time.sleep(5)
            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'anb_' + today_formatted + '.ics'
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
