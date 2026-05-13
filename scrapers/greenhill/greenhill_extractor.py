#!/usr/bin/env python3
"""
Green Hill Farm Schedule Scraper - Selenium Version
Uses Selenium WebDriver to scrape events from www.ghfarm.org/events-1/
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import uuid
import time
import re

# Global variables
year = "2026"
# Format the date as a string in YYYYMMDD format
today = datetime.today()
today_formatted = today.strftime("%Y%m%d")


def setup_driver(headless=True):
    """Setup Chrome WebDriver with options"""
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Suppress unnecessary logging
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=options)
    return driver

def format_time(time):
    try:
        start, end = time.split(" – ")

        def format_tm(time):
            tm, am_pm = time.split(" ")
            hh, mm = tm.split(":")
            if am_pm == "PM" and hh != "12":
                hh = str(int(hh) + 12)
            else:         
                if len(hh) == 1: hh = "0" + hh
            return hh + mm + "00"

        tmstart = format_tm(start)
        tmend = format_tm(end)
        return tmstart,  tmend

    except:
        return '', ''

def format_date(date_str):
    try:
        date_str = date_str.strip()
        month_day, year = date_str.split(", ")
        month, day = month_day.split(" ")
        month = month.strip()
        match month:
            case "January" | "Jan": month = "01"
            case "February" | "Feb": month = "02"
            case "March" | "Mar": month = "03"
            case "April" | "Apr": month = "04"
            case "May" | "May": month = "05"
            case "June" | "Jun": month = "06"
            case "July" | "Jul": month = "07"
            case "August" | "Aug": month = "08"
            case "September" | "Sep": month = "09"
            case "October" | "Oct": month = "10"
            case "November" | "Nov": month = "11"
            case "December" | "Dec": month = "12"
        day = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', day)
        if len(day) == 1: day = "0" + day
        return year + month + day
    except Exception as e:
        print(f"Error in format_date: {date_str} - {e}")
        print("string length:", len(date_str))

def scrape_schedule_page(driver):
    """Scrape events from the schedule page"""
    
    url = "https://www.ghfarm.org/events-1"
    print(f"Navigating to {url}...")
    
    driver.get(url)
    
    # Wait for page to load
    wait = WebDriverWait(driver, 15)
    # print("Waiting for page to load...")
    
    try:
        # Wait for event headers to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="qElViY"]')))
        time.sleep(2)  # Extra time for dynamic content
        print("✓ Page loaded successfully")
    except TimeoutException:
        print(f"\nError: Timeout waiting for content to load")
    
    # Find all event entries
    print("\nExtracting events...")
    events = []
    
    try:
        event_headers = driver.find_elements(By.CSS_SELECTOR, '[class*="qElViY"]')
        print(f"Found {len(event_headers)} potential event elements")
        
        for i, header in enumerate(event_headers, 1):
            try:
                # Find link within header
                link = header.find_element(By.TAG_NAME, 'a')
                url = link.get_attribute('href')
                title_text = link.text.strip()
                # print('url:', url, 'title:', title_text)
                if not title_text or not url:
                    print("Skipped:", title_text)
                    continue                
                event = {
                    'title': title_text,
                    'url': url,
                }                
                events.append(event)   
            except NoSuchElementException:
                continue
            except Exception as e:
                print(f"\nError: {e}")
                print(f"  {i:2d}")
                continue
        
    except Exception as e:
        print(f"Error in scrape_schedule_page: {event_headers} - {e}")
    
    return events
    

def fetch_event_details(driver, event_url):
    """
    Fetch additional details from event page
    Returns dict with time and description
    """
    try:
        # print(f"  Fetching details from: {event_url}")
        driver.get(event_url)
        details = driver.find_element(By.ID,"event-details")
        return details        
    except Exception as e:
        print(f"\nError fetching details: {e}")
        return {'time': '7:30 PM', 'description': ''}
    
def extract_event_info(event_elements, events_extracted, event_url, event_title ):
    """
    Extract Category, More Info, Description, Location, Contact, Phone, and Email
    from event text string
    """
    # print('event_elements:', event_elements.text)

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
        description = event_elements.find_element(By.CSS_SELECTOR,'[data-hook="event-description"]').text
    except:
        print('skipping event_elements:', event_elements.text)
        return

    date_time = event_elements.find_element(By.CSS_SELECTOR,'[data-hook="event-full-date"]').text
    date, time = date_time.rsplit(", ",1)
    date = format_date(date)
    tmstart, tmend = format_time(time)
    dtstart = date + "T" + tmstart + "Z"
    dtend = date + "T" + tmend + "Z"
    location = 'Green Hill Farm, 5329 Mondell Rd, Sharpsburg, MD'
    organization = 'Nearby Events in Sharpsburg'
    if date >= today_formatted:
        result = {
            'category': 'Uncategorized',
            'time': '',
            'more_info_url': event_url,
            'more_info_text': '',
            'summary': event_title,
            'description': description,
            'location': location,
            'organization': organization,
            'location_details': '',
            'contact_name': '',
            'contact_phone': '',
            'contact_email': '',
            'dtstart': dtstart,
            'dtend': dtend,
            'allday': ''
        }    
        events_extracted.append(result)
    
# Escape special characters
def escape_ics(text):
    if not text:
        return ""
    return (text.replace('\\', '\\\\')
                .replace(',', '\\,')
                .replace(';', '\\;')
                .replace('\n', '\\n'))

def create_ics_file(events, filename):
    """Create ICS calendar file from events"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Write ICS header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//Green Hill Farm//Events//EN \n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Green Hill Farm Events\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@greenhill"
            # Format dates
            dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            dtstart = event['dtstart']
            dtend = event['dtend']
            # summary = escape_ics(event['title'])
            summary = event['summary']
            # description = event['description']
            description = escape_ics(event['description'])
            location = event['location']
            organization = event['organization']
            category = event['category']
            url = event.get('more_info_url', '')

            # Write event
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"LOCATION:{location}\n")
            f.write(f"URL:{url}\n")
            f.write(f"CATEGORIES:{category}\n")
            f.write(f"ORGANIZATION:{organization}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:ghfarm.org\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    
    # print("="*70)
    print("Green Hill Farm Schedule Scraper (Selenium)")
    # print("="*70)
    print()
    
    driver = None
    
    try:
        fetch_details = True
        headless = True
        # Setup driver
        print("\n# Setting up Chrome WebDriver...")
        driver = setup_driver(headless=headless)
        if headless:
            print("Running in headless mode (no browser window)")
        else:
            print("Browser window will be visible")
        
        # Scrape schedule page
        events = scrape_schedule_page(driver)        
        if not events:
            print("\n❌ No events found!")
            print("The website structure may have changed.")
            return
        
        print(f"\n✓ Found {len(events)} events")

        events_extracted = []
        
        # Optionally fetch details from each event page
        if fetch_details and events:
            print(f"\nFetching details from {len(events)} event pages...")
            # print("(This may take a minute...)")
            
            for i, event in enumerate(events, 1):
                # if i < 7:
                details = fetch_event_details(driver, event['url'])
                print(362, event['title'])
                if "Happy Hour" not in event['title'] and "Vendor Registration" not in event['title'] and \
                "Sunday Fundays" not in event['title']:
                    extract_event_info(details, events_extracted, event['url'], event['title'])
        
        # Create ICS file
        output_file = 'greenhill_' + today_formatted + '.ics'
        # print(f"\n{'='*70}")
        print(f"Creating ICS file: {output_file}")
        
        create_ics_file(events_extracted, output_file)
        
        # Summary
        print(f"  Total events: {len(events_extracted)}")
        print(f"  Output file: {output_file}")
        
        # Print summary
        # print("\n" + "="*70)
        # # # print("EVENTS SUMMARY")
        # # print("="*70)
        # for i, event in enumerate(events_extracted[:5], 1):
        #     print(f"\n{i}. {event['summary']}")
        #     print(f"   Date: {event['dtstart']}")
        #     print(f"   Location: {event['location']}")
        
        # if len(events_extracted) > 5:
        #     print(f"\n... and {len(events_extracted) - 5} more events")
        
        # print("\n" + "="*70)
        # print(f"Total events: {len(events_extracted)}")
        # print("="*70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
            # print("Done!")

if __name__ == "__main__":
    main()
