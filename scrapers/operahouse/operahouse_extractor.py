#!/usr/bin/env python3
"""
Opera House Schedule Scraper - Selenium Version
Uses Selenium WebDriver to scrape events from operahouselive.com/schedule/
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

def format_time(time, title_line):
    # print('time:', time)
    try:
        if time.startswith("Sunday") or time.startswith("Monday") or time.startswith("Tuesday") or \
        time.startswith("Wednesday") or time.startswith("Thursday") or time.startswith("Friday") or time.startswith("Saturday") or \
        time.startswith("Sun") or time.startswith("Mon") or time.startswith("Tue") or \
        time.startswith("Wed") or time.startswith("Thu") or time.startswith("Fri") or time.startswith("Sat"):
            dow, tm = time.split(", ")
            time = tm
        if " • " in time:
            tm, dt = time.split(" • ")
        else:
            if " at " in time:
                dt, tm = time.split(" at ")
            else:
                tm, dt = time.split(",", 1)
        
        event_date = format_date(dt, title_line)
        tm=tm.replace(" ","").strip().replace("Sunday","").replace("Monday","").replace("Tuesday","").\
            replace("Wednesday","").replace("Thursday","").replace("Friday","").replace("Saturday","").\
            replace("Sun","").replace("Mon","").replace("Tue","").\
            replace("Wed","").replace("Thu","").replace("Fri","").replace("Sat","")
        am_pm = "pm"
        if "am" in time: am_pm = "am"
        tm = tm[0:tm.index(am_pm)]
        tm = tm.replace(am_pm, "")
        hh, mm = tm.split(":")
        if am_pm == "pm" and hh != "12":
            hh = str(int(hh) + 12)
        else:         
            if len(hh) == 1: hh = "0" + hh
        event_time = hh + mm + "00"
        return (event_date + "T" + event_time + "Z"), event_date
    except:
        return '', ''

def format_date(date_str, title_line):
    try:
        # print('date_str:', date_str)
        date_str = date_str.strip()
        month_day = date_str
        month_day = month_day.strip()
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
        print(f"title_line:", title_line)
        print("string length:", len(date_str))

def scrape_schedule_page(driver):
    """Scrape events from the schedule page"""
    
    url = "https://operahouselive.com/schedule/"
    print(f"Navigating to {url}...")
    
    driver.get(url)
    
    # Wait for page to load
    wait = WebDriverWait(driver, 15)
    # print("Waiting for page to load...")
    
    try:
        # Wait for event headers to appear
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h3')))
        time.sleep(2)  # Extra time for dynamic content
        print("✓ Page loaded successfully")
    except TimeoutException:
        print("\nError: Timeout waiting for content to load")
    
    # Find all event entries
    print("\nExtracting events...")
    events = []
    
    try:
        # Find all h3 headers (they contain event links)
        event_headers = driver.find_elements(By.TAG_NAME, 'h3')
        print(f"Found {len(event_headers)} potential event elements")
        
        for i, header in enumerate(event_headers, 1):
            try:
                # Find link within header
                link = header.find_element(By.TAG_NAME, 'a')
                url = link.get_attribute('href')
                title_text = link.text.strip()
                try:
                    if "APR 16 – 19 " in title_text:
                        dt, title = title_text.split("APR 16 – 19 ")
                    else:
                        if " – " in title_text:
                            print(141, title_text)
                            dt, title = title_text.split(" – ")
                        else:
                            if " — " in title_text:
                                print(145, title_text)
                                dt, title = title_text.split(" — ")
                            else:
                                title = None
                                print("Could not upack title from:", title_text)
                except:
                    title = None
                    print("Could not upack title from:", title_text)
                # print('url:', url, 'title:', title)
                if not title or not url:
                    print("Skipped:", title_text)
                    continue                
                event = {
                    'title': title,
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
        details = driver.find_element(By.CLASS_NAME,"entry-content")
        return details        
    except Exception as e:
        print(f"    Error fetching details: {e}")
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
    title_line = ''
    times = []
    location = 'Shepherdstown Opera House, 131 West German Street, Shepherdstown'
    description = ''
    title_line = event_title
    lines = event_elements.text.split("\n")
    for line in lines:
        if line > '':
            if  \
            (("Sunday" in line or "Monday" in line or "Tuesday" in line or "Wednesday" in line or \
            "Thursday" in line or "Friday" in line or "Saturday" in line) and \
            ("January" in line or "February" in line or "March" in line or "April" in line or "May" in line \
            or "June" in line or "July" in line or "August" in line or "September" in line or "October" in line \
            or "November" in line or "December" in line)) or \
            (("Sun" in line or "Mon" in line or "Tue" in line or "Wed" in line or \
            "Thu" in line or "Fri" in line or "Sat" in line) and \
            ("Jan" in line or "Feb" in line or "Mar" in line or "Apr" in line or "May" in line \
            or "Jun" in line or "Jul" in line or "Aug" in line or "Sep" in line or "Oct" in line \
            or "Nov" in line or "Dec" in line)):
                if len(line) < 100:
                    if "Weekend" in line:
                        line = line[line.index(": ") + 2:]
                        line=line.replace("Sunday","").replace("Monday","").replace("Tuesday","").\
                            replace("Wednesday","").replace("Thursday","").replace("Friday","").replace("Saturday","").\
                            replace("Sun","").replace("Mon","").replace("Tue","").\
                            replace("Wed","").replace("Thu","").replace("Fri","").replace("Sat","")
                        mult_times = line.split(",")
                        for mt in mult_times:
                            if mt > ' ':
                                times.append(mt)
                    else:
                        if "Pay-What-You-Can Performance" in line:
                            description = description + line + "\n"
                        else:
                            times.append(line)
                    continue
            if line == title_line: 
                continue
            if line.strip() != "TICKETS":
                description = description + line + "\n"
    organization = 'Shepherdstown Opera House'
    if "Town Run Theater Company" in description:
        organization = 'Town Run Theater Company'
    if "Shepherdstown Film Society" in description:
        organization = 'Shepherdstown Film Society'
    for time in times:
        
        dtstart, event_date = format_time(time, title_line)
        if dtstart > '' and event_date > '':
            if event_date >= today_formatted:
                result = {
                    'category': 'Music & Film & Stage',
                    'time': '',
                    'more_info_url': event_url,
                    'more_info_text': '',
                    'summary': title_line,
                    'description': description,
                    'location': location,
                    'organization': organization,
                    'location_details': '',
                    'contact_name': '',
                    'contact_phone': '',
                    'contact_email': '',
                    'dtstart': dtstart,
                    'dtend': '',
                    'allday': ''
                }    
                events_extracted.append(result)

    return

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
        f.write("PRODID:-//Shepherdstown Opera House//Events//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherdstown Opera House Schedule\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@operahouse"
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
            f.write("SOURCE:operahouselive.com\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    
    # print("="*70)
    print("Opera House Schedule Scraper (Selenium)")
    # # print("="*70)
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
                extract_event_info(details, events_extracted, event['url'], event['title'])
        
        # Create ICS file
        output_file = 'operahouse_' + today_formatted + '.ics'
        # print(f"\n{'='*70}")
        print(f"Creating ICS file: {output_file}")
        
        create_ics_file(events_extracted, output_file)
        
        # Summary
        # print(f"\n{'='*70}")
        # print("✓ SCRAPING COMPLETE!")
        # print(f"{'='*70}")
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
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()
            # print("Done!")

if __name__ == "__main__":
    main()
