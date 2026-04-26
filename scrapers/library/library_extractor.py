#!/usr/bin/env python3
"""
Shepherdstown Public Library Calendar Event Extractor with Browser Automation
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
    print('date_time_string:', date_time_string)

    if date_time_string.count("@") == 2:
        start_date_time, end_date_time = date_time_string.split(" - ")
        st_date, st_time = start_date_time.split(" @ ")
        dtstart = format_date(st_date) + "T" + format_time(st_time) + "Z"
        en_date, en_time = end_date_time.split(" @ ")
        dtend = format_date(en_date) + "T" + format_time(en_time) + "Z"
        start_description_with_date_time = True
    else:
        if "@" not in date_time_string:
            all_day = True
            if "-" in date_time_string:
                start_date, end_date = date_time_string.split(" - ")
                dtstart = format_date(start_date) + "T000000Z"
                dtend = format_date(end_date) + "T000000Z"
                start_description_with_date_time = True
                # dtend = format_date(end_date) + "T000000Z"
            else:
                start_date = format_date(date_time_string)
                dtstart = start_date + "T000000Z"
        else:
            # print('date_time_string:', date_time_string)
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

    print('dtstart:', dtstart, 'dtend:', dtend, 'all_day:', all_day)

    return dtstart, dtend, all_day, start_description_with_date_time

def format_time(time):
    # time = time.replace(":", "")
    time=time.replace(" ","")
    am_pm = "pm"
    if "am" in time: am_pm = "am"
    time = time.replace(am_pm, "")
    hh, mm = time.split(":")
    if am_pm == "pm" and hh != "12":
        hh = str(int(hh) + 12)
    else:         
        if len(hh) == 1: hh = "0" + hh
    return (hh + mm + "00")


def format_date(date_str):
    #remove day of week
    # month_day_part = date_str.split(", ")[1]
    date_str = date_str.strip()
    month, day = date_str.split(" ")
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

def click_next_month_button(driver, wait):
    """Click the List button on the calendar page"""
    print("Looking for Next Month button...")
    # driver.switch_to.frame("cw_frame")
    try:
        button = driver.find_element(By.XPATH, "//a[@title='Next Events']")
        button.click()
        # WebDriverWait(driver, 50)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME,"tribe-events-c-top-bar__datepicker-desktop")))
        # class="tribe-events-c-top-bar__datepicker-desktop tribe-common-a11y-hidden"
        WebDriverWait(driver, 25)
        time.sleep(5)
        print("✓ Clicked Next Month button")
        # time.sleep(15)
        return True
    except:
        return False

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
        title_link = event_elements.find_element(By.CLASS_NAME, "tribe-events-calendar-list__event-title-link")
    except:
        return result    
    title = title_link.text.strip()
    title_href = title_link.get_attribute("href")
    # print('title:', title, title_href)
    date_time_string = event_elements.find_element(By.CLASS_NAME, "tribe-events-calendar-list__event-datetime").text
    dtstart, dtend, all_day, start_description_with_date_time = extract_date_times(date_time_string)
    try:
        location = event_elements.find_element(By.CLASS_NAME, "tribe-events-calendar-list__event-venue-title").text.strip()
    except:
        location = ''
    # print('location:', location)
    try:
        address = event_elements.find_element(By.CLASS_NAME, "tribe-events-calendar-list__event-venue-address").text.replace(", WV, United States","")
        if address > '':
            location += ", " + address
    except:
        pass
    description = ''
    if start_description_with_date_time: description = date_time_string + "\n\n"
    try:
        description += event_elements.find_element(By.CLASS_NAME, "tribe-events-calendar-list__event-description").text
    except:
        pass
    if "FOSL" in description or "Friends of Shepherdstown Library" in description:
        organization = "Friends of Shepherdstown Library"
    else:
        organization = "Shepherdstown Public Library"
    # try:
    #     category = event_elements.find_element(By.CLASS_NAME, "tec_series_marker__title").text
    # except:
    #     category = ''    
    category = []
    category = category_matcher.categorize_by_keywords(title)
    if category == []:
        category = ["Uncategorized"]

    result['category'] = category
    result['more_info_url'] = title_href
    result['more_info_text'] = title
    result['summary'] = title
    result['description'] = description
    result['location'] = location
    result['organization'] = organization
    result['dtstart'] = dtstart
    result['dtend'] = dtend    
    result['allday'] = all_day
    # print("result:", result)
    return result

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//sheplibrary.org//Events//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherdstown Events Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@sheplibrary.info"
            
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
            category = ', '.join(event['category'])
            url = event.get('more_info_url', '')
            organization = event['organization']
            
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"LOCATION:{location}\n")
            f.write(f"ORGANIZATION:{organization}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"CATEGORIES:{category}\n")
            # f.write(f"ORGANIZATION:Shepherdstown Public Library\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:sheplibrary.org\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    print("="*70)
    print("Shepherdstown Public Library Calendar Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=False)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://www.sheplibrary.org/events/list/"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        print("Waiting for page to load...")
        time.sleep(5)
        
        events_extracted = []
        pages_scraped = 0

        # Extract up to a maximum pages. Each will have between 4 and 8 days of events.
        max_pages = 12
        while pages_scraped < max_pages:
            pages_scraped += 1
            events = driver.find_elements(By.CSS_SELECTOR, ".tribe-events-calendar-list__event-row")
            for event in events:
                # print('pages_scraped:', pages_scraped)
                event_elements = extract_event_info(event)
                if event_elements['summary'] != "":
                    events_extracted.append(event_elements)
                # break

            # Click next month button
            if pages_scraped < max_pages:
                cont = click_next_month_button(driver, wait)
                if cont == False: pages_scraped = max_pages
                else: time.sleep(5)
            
        if not events_extracted:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'library_' + today_formatted + '.ics'
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
