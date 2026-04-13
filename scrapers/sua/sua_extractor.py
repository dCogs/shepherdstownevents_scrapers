#!/usr/bin/env python3
"""
Shepherdstown University Athletics Extractor with Browser Automation
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
from selenium.webdriver.support.ui import Select
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

def format_time(time):
    # time = time.replace(":", "")
    # print('time:', time)
    if time == "POSTPONED":
        return "POSTPONED"
    time=time.replace(" ","").strip()
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
    # print('date_str:', date_str)
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    # print(106, date_str)
    # date_str = date_str.strip()
    # print(108)
    dow, month_day, year = date_str.split(", ")
    month, formatted_day = month_day.split(" ")
    day = re.sub(r'(\d+)(?:ST|ND|RD|TH)', r'\1', formatted_day, flags=re.IGNORECASE)

    match month:
        case "JANUARY": month = "01"
        case "FEBRUARY": month = "02"
        case "MARCH": month = "03"
        case "APRIL": month = "04"
        case "MAY": month = "05"
        case "JUNE": month = "06"
        case "JULY": month = "07"
        case "AUGUST": month = "08"
        case "SEPTEMBER": month = "09"
        case "OCTOBER": month = "10"
        case "NOVEMBER": month = "11"
        case "DECEMBER": month = "12"
    day = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', day)
    if len(day) == 1: day = "0" + day
    # print('month:', month, ' day:', day)
    return year + "-" + month + "-" + day

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//shepherd.edu/calendar//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherd University Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@sua"
            
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
            category = escape_ics(event['category'])
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
            f.write(f"ORGANIZATION:Shepherd University Athletics\n")           
            if url:
                f.write(f"URL:{url}\n")
            f.write(f"organization:Shepherd University Athletics\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:shepherdrams.com\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    print("="*70)
    print("Shepherdstown University Athletics Calendar Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://shepherdrams.com/calendar?vtype=list"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 200)
        print("Waiting for page to load...")
        time.sleep(8)
        
        dropdown_element = driver.find_element(By.ID, 'selected_location')
        select = Select(dropdown_element)
        select.select_by_visible_text("Home")
        go_button = driver.find_element(By.CSS_SELECTOR, "button.sidearm-calendar-go-button")
        go_button.click()
        wait = WebDriverWait(driver, 200)
        print("Waiting for page to load...")
        time.sleep(10)

        date_input = driver.find_element(By.ID, "id-textbox-1")

        events_extracted = []
        # curr_date = ''
        last_date_value = date_input.get_attribute("placeholder")

        weeks_scraped = 0
        max_weeks_scraped = 5
        while weeks_scraped < max_weeks_scraped:
            weeks_scraped += 1
            day_blocks = driver.find_elements(By.CLASS_NAME, "sidearm-calendar-schedule-day")
            # print('')
            # print(283, len(day_blocks))
            for day_block in day_blocks:
                day = day_block.find_element(By.TAG_NAME, "h4")
                # print('')
                # print('day:', day.text)
                curr_date = format_date(day.text)
                # print('curr_date:', curr_date)
                events = day_block.find_elements(By.CLASS_NAME, "sidearm-calendar-schedule-event")
                for event in events:
                    h5 = event.find_element(By.TAG_NAME, "h5")
                    span_lines = h5.find_elements(By.TAG_NAME, "span")
                    # print('event:', span_lines.text)
                    # span_lines = event.find_elements(By.TAG_NAME, "span")
                    event_sport = ''
                    event_time = ''
                    event_opponent = ''
                    event_location = ''
                    dtstart = ''

                    for span_line in span_lines:
                        text_content = span_line.get_attribute('textContent')
                        text_context = span_line.get_attribute("data-bind")
                        # print('text_context:', text_context, 'text_content:', text_content)
                        if "sport.title" in text_context: event_sport = text_content
                        if "opponent.title" in text_context: event_opponent = text_content
                        if "noplay_text" in text_context:
                                print('skipping', text_content)
                                event_sport = ''
                                event_time = ''
                                event_opponent = ''
                                event_location = ''
                                dtstart = ''
                                continue
                        if "time" in text_context: 
                            # print('text_context:', text_context, ' text_content:', text_content)
                            if text_content == "TBA" or text_content == '':
                                print('skipping', text_content)
                                event_sport = ''
                                event_time = ''
                                event_opponent = ''
                                event_location = ''
                                dtstart = ''
                                continue
                            event_time = format_time(text_content)
                            if event_time != "POSTPONED":
                                # print('event_time:', time)
                                dtstart = curr_date.replace("-","") + "T" + event_time + "Z"
                        if "location" in text_context: event_location = text_content
                        # print('event_sport:', event_sport, 'event_time:', event_time, 'event_opponent:', event_opponent, 'event_location:', event_location)

                        summary = "Shepherd U " + event_sport + " vs " + event_opponent
                        if event_time == "POSTPONED":
                            summary = "POSTPONED - " + summary

                        if event_sport != '' and event_time != '' and event_opponent != '' and event_location != '':
                            # print('resulting...')
                            result = {
                                'category': 'Sports',
                                'time': '', 
                                'more_info_url': 'https://shepherdrams.com/calendar',
                                'more_info_text': '',
                                'summary': summary,
                                'description': '',
                                'location': event_location,
                                'location_details': '',
                                'contact_name': '',
                                'contact_phone': '',
                                'contact_email': '',
                                'dtstart': dtstart,
                                'dtend': '',
                                'allday': ''
                            }
                            events_extracted.append(result)
                            event_sport = ''
                            event_time = ''
                            event_opponent = ''
                            event_location = ''
                            dtstart = ''

            # date_object = datetime.strptime(curr_date, "%Y-%m-%d")
            # input_value = date_input.get_attribute("placeholder")
            # print('')
            # print('last_date_value:', last_date_value)
            date_object = datetime.strptime(last_date_value, "%m/%d/%Y")
            # print('date_object:', date_object)
            new_date_object = date_object + timedelta(days=7)
            new_date_value = new_date_object.strftime("%m/%d/%Y")
            # print('new_date_value:', new_date_value)
            date_input.clear()
            date_input.send_keys(new_date_value)
            go_button.click()
            last_date_value = new_date_value
            wait = WebDriverWait(driver, 200)
            print("Waiting for page to load...")
            time.sleep(5)

            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'sua_' + today_formatted + '.ics'
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
