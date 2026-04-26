#!/usr/bin/env python3
"""
Shepherdstown.info Calendar Event Extractor with Browser Automation
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
import sys
import os
# Get the absolute path of the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path of the parent directory
parent_dir = os.path.dirname(current_dir)
# Insert the parent directory path into sys.path
sys.path.insert(0, parent_dir)
# Shepherdstown.info is the only scraper that uses the generic category_matcher
import category_matcher


# Global variables
# Format the date as a string in YYYYMMDD format
today = datetime.today()
now = datetime.now()
# Extract the year
year_int = now.year
year = str(year_int)
print("year:", year)
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

def format_date(date_str):
    #remove day of week
    month_day_part = date_str.split(", ")[1]
    month, day = month_day_part.split(" ")
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

def click_list_button(driver, wait):
    """Click the List button on the calendar page"""
    # print("Looking for List button...")
    driver.switch_to.frame("cw_frame")
    button = driver.find_element(By.XPATH, "//*[@id='btn_view_list']")
    button.click()
    print("✓ Clicked List button")
    return True

def click_next_month_button(driver, wait):
    """Click the List button on the calendar page"""
    # print("Looking for Next Month button...")
    # driver.switch_to.frame("cw_frame")
    button = driver.find_element(By.XPATH, "//a[@title='Go to next month']")
    button.click()
    print("✓ Clicked Next Month button")
    return True

def extract_events_from_list(date, event_elements):
    """Extract events from the list view"""
    # print("Extracting event for date", date)
    elements = extract_event_info(date, event_elements)
    return elements

def extract_event_info(date, event_elements):
    """
    Extract Category, More Info, Description, Location, Contact, Phone, and Email
    from event text string
    """
    try:
        # print("extract_event_info")
        text = event_elements.text
        # print('')
        # print('text:', text)

        result = {
            'category': '',
            'time': '',
            'more_info_url': '',
            'more_info_text': '',
            'summary': '',
            'organization': '',
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
        
        exclude_urls = ['sheplibrary.org', 'foslwv.org', 'speakstoryseries.com', 'shepherd.edu/music', 'shepherdrams.universitytickets.com',
                        'shepherd.edu/sustainable-agriculture', 'townrunwatershed.org', 'friendswv.org', 'fourseasonsbooks.com',
                        'operahouselive.com', 'shepherdstownoperahouse.thundertix.com', 'ShepherdstownMysteryWalks.com',
                        'shepherdstowncommunityclub.org'
                        ]
        # Extract More Info section
        # for elem in event_elements:
        #     print('elem text:', elem.text, ' class:', elem.get_attribute("class"))
        # title_url = event_elements.find_element(By.CLASS_NAME, "cat279542")
        # if not title_url:
        #     print("No title found -- skipping")
        #     return result
        # title = title_url.text
        # url = title_url.get_attribute("href")
        # print ('title:', title, 'url:', url)

        more_info_match = re.search(r'More Info\s*\n(.*?)(?=Location Details:|Contact\n|Location\n|$)', text, re.IGNORECASE | re.DOTALL)
        if more_info_match:
            # print('more_info_match:', more_info_match)
            more_info_section = more_info_match.group(1).strip()
            
            # Extract URL from More Info (handle URLs that might have spaces)
            # First line after "More Info" is typically the URL
            lines = more_info_section.split('\n')

            # for ln in lines:
            #     print('148 line:', ln)

            if lines:
                first_line = lines[0].strip()
                # Remove spaces from URL (common OCR/copy error)
                # print('first_line:', first_line)
                if 'www.' in first_line or 'http' in first_line:
                    result['more_info_url'] = first_line.replace(' ', '')
                    # Look at the url for organizations that are imported from other scrapers and skip if present
                    for url in exclude_urls:
                        if url in result['more_info_url']:
                            # print('')
                            # print('skipping ', result['more_info_url'])
                            result['dtstart'] = ''
                            return result
            
            # Rest of More Info is the text
            result['more_info_text'] = more_info_section
            # print('more_info_text:', result['more_info_text'])
        else:
            # If there was no more_info_match, look at the lines below category_match to pull summary and description
            # category_match = re.search(r'Category\s*\n(.*?)(?=Location Details:|Contact\n|Location\n|$)', text, re.IGNORECASE | re.DOTALL)
            category_match = re.search(r'Categor(?:y|ies)\s*\n(.*?)(?=Location Details:|Contact\n|Location\n|$)', text, re.IGNORECASE | re.DOTALL)
            if category_match == None:
                print('category_match = None. Here is the text:\n')
                print(text)
            else:                      
                category_section = category_match.group(1).strip()
                lines = category_section.split('\n')
        if lines:
            # Extract description (everything after the first line/URL)
            desc_lines = []
            for i, line in enumerate(lines):
                line = line.strip()
                # Skip the first line (URL) and very short lines
                if i > 0 and line:
                    if ("Time: " in line or "Dates: " in line) and result['summary'] == '':
                        if "Time: " in line: result['summary'] = line[0:line.index("Time: ")].strip()
                        if "Dates: " in line: result['summary'] = line[0:line.index("Dates: ")].strip()
                    else:
                        desc_lines.append(line)
            result['description'] = '\n'.join(desc_lines).strip()

        if result['summary'] != '':
            category = []
            category = category_matcher.categorize_by_keywords(result['summary'])
            result['category'] = category

        def format_datetime(date, time):
            # time = time.replace(":", "")
            am_pm = "pm"
            if "am" in time: am_pm = "am"
            time = time.replace(am_pm, "")
            # print('time:', time)
            if "ALL DAY" in time.upper():
                return "ALL DAY"
            else:
                hh, mm = time.split(":")
                if am_pm == "pm" and hh != "12":
                    hh = str(int(hh) + 12)
                else:         
                    if len(hh) == 1: hh = "0" + hh
            return (date + "T" + hh + mm + "00Z")
                
        # Extract time
        time_details_match = re.search(r'Time:\s*([^\n]+)', text, re.IGNORECASE).group(1).strip()
        if time_details_match:
            result['time'] = time_details_match
            dtstart = ''
            dtend = ''
            if ' - ' in time_details_match:
                dtstart, dtend = time_details_match.split(" - ")
            else: 
                dtstart = time_details_match
            dtstart = format_datetime(date, dtstart)
            if dtstart == "ALL DAY":
                # print(text)
                result['allday'] = 'true'
                dtstart = date + "T" + "000000Z"
                dtend = date + "T" + "235959Z"
            else:
                if dtend != '': dtend = format_datetime(date, dtend)
            result['dtstart'] = dtstart
            result['dtend'] = dtend

        
        # Extract Location Details
        location_details_match = re.search(r'Location Details:\s*([^\n]+)', text, re.IGNORECASE)
        if location_details_match:
            result['location_details'] = location_details_match.group(1).strip()
            description = result['description']
            description += '\n\n<b>Location Details:</b> ' + result['location_details'].strip()
            result['description'] = description
        
        # Extract Contact section
        contact_match = re.search(r'Contact\s*\n\s*([^\n]+)', text, re.IGNORECASE)
        if contact_match:
            contact_line = contact_match.group(1).strip()
            # Parse contact line: "Name, Phone, Email"
            parts = [p.strip() for p in contact_line.split(',')]
            if len(parts) >= 1:
                result['contact_name'] = parts[0]
            if len(parts) >= 2:
                # Extract phone (remove any non-digits for storage, but keep original)
                phone = parts[1].strip()
                result['contact_phone'] = phone
            if len(parts) >= 3:
                # Remove spaces from email (common OCR/copy error)
                result['contact_email'] = parts[2].strip().replace(' ', '')
            description = result['description']
            description += '\n\n<b>Contact Info:</b> ' + result['contact_name'].strip() + \
                ' ' + result['contact_phone'] + ' ' + result['contact_email']
            result['description'] = description

        # Extract Location (at the end)
        location_match = re.search(r'Location\s*\n\s*([^\n]+?)(?:\s*$|\n|$)', text, re.IGNORECASE)
        if location_match:
            result['location'] = location_match.group(1).strip()

        # Set the organization when you want it different from location
        if "Two Rivers Chamber Orchestra" in result['summary']:
            result['organization'] = "Two Rivers Chamber Orchestra"
        else:
            # if "Shepherd Univ" in result['location']:
            #     result['organization'] = 'Shepherd University Concerts and Events'
            # else:
            if result['summary'] == "American Conservation Film Festival":
                result['organization'] = result['summary']
            else:
                if result['summary'] == "Family, Friends & Fear":
                    result['organization'] = "Artful Codgers"
                    category.append('Music & Film & Stage')
                else:
                    result['organization'] = result['location']
        if result['location'] == "Public Library (Shepherdstown)" : 
            result['location'] = "Shepherdstown Public Library"
            result['organization'] = "Friends of Shepherdstown Library"
        if result['location'] == "Shepherd Univ - Frank Center": 
            if "Turning Pointe Dance Company" in description: result['organization'] = "Turning Pointe Dance Company"
            else:
                if result['summary'] != "American Conservation Film Festival":
                    result['organization'] = "Shepherd University"
        if result['location'] == "Shepherdstown Opera House" : 
            result['location'] = "Shepherdstown Opera House, 131 West German Street, Shepherdstown"
            if "Town Run Theater Company" in result['summary']:
                result['organization'] = "Town Run Theater Company"
            if "Shepherdstown Film Society" in result['summary']:
                result['organization'] = "Shepherdstown Film Society"
            if result['more_info_url'] == '':
                result['more_info_url'] = "https://operahouselive.com/schedule/"
            if "Music & Film & Stage" not in result['category']:
                result['category'].append('Music & Film & Stage')
        # print(281, result['location'])
        if result['location'] == "Shepherdstown Fire Hall":
            result['organization'] = "Shepherdstown Fire Department"
        if result['location'] == "Shepherd Univ - Student Center":
            result['organization'] = "Shepherd University"
        if result['location'] == "Skull City Studio & The Roving Peregrine Theater Company":
            result['organization'] = "Skull City Studio"
        if result["organization"] == "Shepherd Univ - Byrd Center for Congressional History and Education" or \
        "shepherd.edu/" in result['more_info_url']:
            result["organization"] = "Shepherd University"
        if result['location'] == "Make It Shepherdstown":
            result['organization'] = "Make It Shepherdstown"
            result['location'] = "109 South Princess Street, Shepherdstown"
            result['more_info_url'] = "https://www.makeitshepherdstown.biz/#features"
        if result['location'] == "Historic Shepherdstown Museum at the Entler Hotel":
            result['organization'] = "Historic Shepherdstown & Museum"
        if result['location'] == "USGS Eastern Ecological Science Center":
            result['location'] = "USGS Eastern Ecological Science Center, 11649 Leetown Road, Kearneysville"
        if result['location'] == "Community Club (War Memorial Building)" and "SCC" in result['summary']:
            result['organization'] = "Shepherdstown Community Club"
            result['location'] = "War Memorial Building, 102 E. German Street"
        if result['location'] == "Shepherd Univ - Studio 112":
            result['organization'] = "Shepherd University"
            result['location'] = "Shepherd Univ - Studio 112, 92 West Campus Drive, Shepherdstown"

        # These are brought in on other scrapers
        if result['location'] == "Shepherd Univ - Shipley Recital Hall" or result['location'] == "Shepherd Univ - Tabler Farm" or \
        result['location'] == "Shepherd Univ - Marinoff Theater":
            result['dtstart'] = ''
            return result
        
        if ("Shepherdstown Live" in result['summary'] and "First Friday Music" in result['summary']) or \
            "Town Council Meeting" in result['summary']:
            result['organization'] = "Town of Shepherdstown"

        # Skip organizations that come in from other scrapers
        if result['organization'] == 'Friends of Shepherdstown Library' or \
        "Blue Ridge Arts & Crafts" in result['summary']:
            result['dtstart'] = ''
            return result
        
        if result['summary'] == "Shepherdstown Gay Pride Parade":
            result['organization'] = "Miscellaneous"
            result['more_info_url'] = "https://www.facebook.com/events/german-st-shepherdstown-wv-25443-united-states/2nd-annual-shepherdstown-gay-pride-parade/1585216485841054/"

        if result['location'] == "Grapes and Grains Gourmet":
            result['location'] = "Grapes and Grains Gourmet, 110 E German St, Shepherdstown"

        # Check for TICKET LINK they do for Opera House sometimes
        ticket_link = re.search(r'TICKET LINK\s*\n(.*?)', text)
        if ticket_link:
            # print('ticket_link:')
            anchor = event_elements.find_element(By.CSS_SELECTOR, "a[rel='noopener']")
            # Or using XPath:
            # anchor = driver.find_element(By.XPATH, "//a[@rel='noopener noreferrer']")
            href = anchor.get_attribute("href")
            result['more_info_url'] = href
            description = result['description']
            description = description.replace('TICKET LINK', '')
            result['description'] = description
            # print(href)

        description = result['description']
        description = '<p>' + description + '</p'
        result['description'] = description

        # 
        if "mohaluwellness.com" in description or "mohaluwellness" in result['contact_email']:
            result['organization'] = "Mohalu Wellness"

        if "smad.us" in result['more_info_url']:
            result['organization'] = "Shepherdstown Music & Dance"

        if "SAIL" in description and "shepherdstownsail.org" in description:
            result['organization'] = "Shepherdstown Area Independent Living"
            result['more_info_url'] = "https://sail.clubexpress.com/"

        if "Experience Shepherdstown" in description:
            result['organization'] = "Experience Shepherdstown"

        for url in exclude_urls:
            if url in result['more_info_url']:
                # print('')
                # print('skipping ', result['more_info_url'])
                result['dtstart'] = ''
                return result
        
        if "Speak Story Series" in result['summary'] or \
        "Shepherdstown Mystery Walks" in result['description'] or \
        "May Day Celebration" in result['summary']:
            result['dtstart'] = ''
            return result
        
        # print("result:", result)
        return result
    except Exception as e:
        print("\nError while processing:", event_elements.text)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        result['dtstart'] = ''
        return result

def format_phone(phone):
    """Format phone number to (xxx) xxx-xxxx"""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def create_ics_file(events, filename):
    """Create ICS file from events"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//Shepherdstown.info//Events//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Shepherdstown Events Calendar\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Write events
        for event in events:
            if not event.get('dtstart'):
                continue
            
            # Generate UID
            uid = f"{event['dtstart']}-{uuid.uuid5(uuid.NAMESPACE_DNS, event['summary'].strip())}@shepherdstown.info"
            
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
            organization = escape_ics(event['organization'])
            description = escape_ics(event['description'])
            url = event.get('more_info_url', '')
            if len(event['category']) > 0:
                category = ', '.join(event['category'])
            else:
                category = 'Uncategorized'
            # category = ', '.join(event['category'])
            
            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp}\n")
            f.write(f"DTSTART:{dtstart}\n")
            f.write(f"DTEND:{dtend}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"ORGANIZATION:{organization}\n")
            f.write(f"LOCATION:{location}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"CATEGORIES:{category}\n")
            if url:
                f.write(f"URL:{url}\n")
            f.write("STATUS:CONFIRMED\n")
            f.write("SOURCE:shepherdstown.info\n")
            f.write("SEQUENCE:0\n")
            f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def main():
    """Main function"""
    print("="*70)
    print("Shepherdstown.info Calendar Event Extractor")
    print("="*70)
    print()
    
    driver = None
    try:
        # Setup driver
        print("Setting up Chrome WebDriver...")
        driver = setup_driver(headless=True)  # Set to True to run in background
        
        # Navigate to calendar page
        url = "https://shepherdstown.info/events/"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        print("Waiting for page to load...")
        time.sleep(3)
        
        # Click List button
        click_list_button(driver, wait)

        events = []
        months_scraped = 0

        # Extract up to a maximum months. Keep 1 or 2 while testing
        max_months = 4
        while months_scraped < max_months:
            months_scraped += 1
            elements = driver.find_elements(By.CSS_SELECTOR, ".daycell, .event_container")
            date = None
            skip_date = False
            # Loop through the found elements
            for element in elements:
                class_name = element.get_attribute("class")
                if class_name == "daycell":
                    # print("Extracting date:", element.text)
                    date = format_date(element.text)
                    skip_date = False
                    if date < today_formatted: skip_date = True
                else:
                    if date != None and skip_date == False:
                        event_elements = extract_events_from_list(date, element)
                        if event_elements['dtstart'] != '':
                            events.append(event_elements)
                        # break

            # Click next month button
            click_next_month_button(driver, wait)
            
        if not events:
            print("\nNo events found. The page structure may have changed.")
        else:
            # Save to ICS
            output_file = 'shepinfo_' + today_formatted + '.ics'
            print(f"\nSaving {len(events)} events to {output_file}...")
            create_ics_file(events, output_file)
            print(f"✓ ICS file created successfully!")
            
            # Print summary
            print("\n" + "="*70)
            print("EVENTS SUMMARY")
            print("="*70)
            for i, event in enumerate(events[:5], 1):
                print(f"\n{i}. {event['summary']}")
                print(f"   Date: {event['dtstart']}")
                print(f"   Location: {event['location']}")
            
            if len(events) > 5:
                print(f"\n... and {len(events) - 5} more events")
            
            print("\n" + "="*70)
            print(f"Total events: {len(events)}")
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
