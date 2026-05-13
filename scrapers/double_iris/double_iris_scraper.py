#!/usr/bin/env python3
"""
Double Iris Yoga and Massage Schedule Scraper
Extracts yoga class schedule and creates ICS calendar file
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import time
import re

def setup_driver(headless=True):
    """Setup Chrome WebDriver with options"""
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=options)
    return driver

def parse_time(time_str):
    """Parse time string to datetime.time object"""
    try:
        # Handle formats like "9:00 AM", "10:30am", "9am"
        time_str = time_str.strip().upper().replace('.', '')
        
        # Try with minutes
        for fmt in ['%I:%M %p', '%I:%M%p', '%H:%M']:
            try:
                return datetime.strptime(time_str, fmt).time()
            except:
                continue
        
        # Try without minutes
        for fmt in ['%I %p', '%I%p']:
            try:
                return datetime.strptime(time_str, fmt).time()
            except:
                continue
        
        return None
    except:
        return None

def parse_day_of_week(day_str):
    """Convert day string to weekday number (0=Monday)"""
    days = {
        'MONDAY': 0, 'MON': 0,
        'TUESDAY': 1, 'TUE': 1, 'TUES': 1,
        'WEDNESDAY': 2, 'WED': 2,
        'THURSDAY': 3, 'THU': 3, 'THUR': 3, 'THURS': 3,
        'FRIDAY': 4, 'FRI': 4,
        'SATURDAY': 5, 'SAT': 5,
        'SUNDAY': 6, 'SUN': 6
    }
    return days.get(day_str.upper().strip())

def get_next_occurrence(weekday, time_obj, weeks=12):
    """
    Generate next occurrences of a weekly class
    
    Args:
        weekday: 0=Monday, 6=Sunday
        time_obj: datetime.time object
        weeks: Number of weeks to generate
    """
    today = datetime.now()
    days_ahead = weekday - today.weekday()
    
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    
    occurrences = []
    for i in range(weeks):
        next_date = today + timedelta(days=days_ahead + (i * 7))
        occurrence = datetime.combine(next_date.date(), time_obj)
        occurrences.append(occurrence)
    
    return occurrences

def scrape_schedule(driver):
    """Scrape the yoga schedule page"""
    
    url = "https://www.doubleirisyogaandmassage.com/schedule"
    print(f"Navigating to {url}...")
    
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    
    # print("Waiting for page to load...")
    time.sleep(5)  # Give extra time for dynamic content
    
    # Save page source for debugging
    page_source = driver.page_source
    
    events = []
    
    # Try multiple strategies to find schedule content
    
    # Strategy 1: Look for embedded calendar/scheduling widget
    try:
        print("\nLooking for scheduling widget...")
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"Found {len(iframes)} iframes")
        
        for i, iframe in enumerate(iframes):
            try:
                print(f"Checking iframe {i+1}...")
                driver.switch_to.frame(iframe)
                time.sleep(2)
                
                # Look for schedule elements
                schedule_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="event"], [class*="class"], [class*="schedule"]')
                if schedule_elements:
                    print(f"  Found {len(schedule_elements)} potential schedule elements")
                
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue
    except Exception as e:
        print(f"Error checking iframes: {e}")
    
    # Strategy 2: Look for text content describing schedule
    try:
        print("\nLooking for schedule text content...")
        # Get all text content
        body = driver.find_element(By.TAG_NAME, 'body')
        body_text = body.text
        
        print(f"Page text length: {len(body_text)} characters")
        
        # Look for schedule patterns in text
        # Common patterns: "Monday 9:00 AM - Yoga Class"
        lines = body_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for day + time pattern
            day_pattern = r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*[:\-]?\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))'
            match = re.search(day_pattern, line, re.IGNORECASE)
            
            if match:
                day_str = match.group(1)
                time_str = match.group(2)
                
                # Extract class name (usually after time)
                class_name = line.split(time_str)[-1].strip()
                if class_name.startswith('-') or class_name.startswith(':'):
                    class_name = class_name[1:].strip()
                
                print(f"  Found: {day_str} {time_str} - {class_name}")
                
                weekday = parse_day_of_week(day_str)
                time_obj = parse_time(time_str)
                
                if weekday is not None and time_obj:
                    events.append({
                        'day': day_str,
                        'weekday': weekday,
                        'time': time_str,
                        'time_obj': time_obj,
                        'title': class_name or 'Yoga Class',
                        'recurring': True
                    })
    except Exception as e:
        print(f"Error parsing text content: {e}")
    
    # Strategy 3: Look for structured elements
    try:
        print("\nLooking for structured schedule elements...")
        
        # Common selectors for schedule listings
        selectors = [
            '.schedule-item',
            '.class-item',
            '.event-item',
            '[class*="schedule"]',
            '[class*="class-list"]',
            'table tr',
            '.sqs-block-content'
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  Found {len(elements)} elements with selector: {selector}")
                    
                    for elem in elements[:10]:  # Check first 10
                        text = elem.text.strip()
                        if len(text) > 10 and len(text) < 200:
                            print(f"    Sample: {text[:80]}...")
            except:
                continue
    except Exception as e:
        print(f"Error checking structured elements: {e}")
    
    return events, body_text if 'body_text' in locals() else page_source[:1000]

def create_ics_file(events, filename):
    """Create ICS calendar file from events"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Write ICS header
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//Double Iris Yoga and Massage//Schedule//EN\n")
        f.write("CALSCALE:GREGORIAN\n")
        f.write("METHOD:PUBLISH\n")
        f.write("X-WR-CALNAME:Double Iris Yoga Schedule\n")
        f.write("X-WR-TIMEZONE:America/New_York\n")
        
        # Process each event
        for event in events:
            if not event.get('time_obj'):
                continue
            
            # Generate occurrences for next 12 weeks
            occurrences = get_next_occurrence(event['weekday'], event['time_obj'], weeks=12)
            
            for occurrence in occurrences:
                # Calculate end time (assume 60 min class)
                end_time = occurrence + timedelta(minutes=60)
                
                # Generate UID
                uid = f"{occurrence.strftime('%Y%m%d%H%M%S')}-{abs(hash(event['title']))}@doubleirisyoga.com"
                
                # Format dates for ICS
                dtstamp = datetime.now().strftime('%Y%m%dT%H%M%S')
                dtstart = occurrence.strftime('%Y%m%dT%H%M%S')
                dtend = end_time.strftime('%Y%m%dT%H%M%S')
                
                # Escape special characters
                def escape_ics(text):
                    if not text:
                        return ""
                    return (text.replace('\\', '\\\\')
                               .replace(',', '\\,')
                               .replace(';', '\\;')
                               .replace('\n', '\\n'))
                
                summary = escape_ics(event['title'])
                description = escape_ics(f"Recurring weekly {event['day']} class at {event['time']}")
                location = "Double Iris Yoga and Massage\\, 201 West Washington Street\\, Charles Town\\, WV 25414"
                
                # Write event
                f.write("BEGIN:VEVENT\n")
                f.write(f"UID:{uid}\n")
                f.write(f"DTSTAMP:{dtstamp}\n")
                f.write(f"DTSTART:{dtstart}\n")
                f.write(f"DTEND:{dtend}\n")
                f.write(f"SUMMARY:{summary}\n")
                f.write(f"DESCRIPTION:{description}\n")
                f.write(f"LOCATION:{location}\n")
                f.write(f"URL:https://www.doubleirisyogaandmassage.com/schedule\n")
                f.write("STATUS:CONFIRMED\n")
                f.write("SEQUENCE:0\n")
                f.write("END:VEVENT\n")
        
        # Write footer
        f.write("END:VCALENDAR\n")

def create_sample_schedule():
    """
    Create sample schedule based on typical yoga studio offerings
    This is a fallback if the page doesn't have parseable schedule
    """
    print("\nCreating sample schedule based on typical yoga studio hours...")
    
    sample_events = [
        {
            'day': 'Monday',
            'weekday': 0,
            'time': '9:00 AM',
            'time_obj': datetime.strptime('9:00 AM', '%I:%M %p').time(),
            'title': 'Morning Yoga',
            'recurring': True
        },
        {
            'day': 'Monday',
            'weekday': 0,
            'time': '6:00 PM',
            'time_obj': datetime.strptime('6:00 PM', '%I:%M %p').time(),
            'title': 'Evening Yoga',
            'recurring': True
        },
        {
            'day': 'Wednesday',
            'weekday': 2,
            'time': '9:00 AM',
            'time_obj': datetime.strptime('9:00 AM', '%I:%M %p').time(),
            'title': 'Morning Yoga',
            'recurring': True
        },
        {
            'day': 'Wednesday',
            'weekday': 2,
            'time': '6:00 PM',
            'time_obj': datetime.strptime('6:00 PM', '%I:%M %p').time(),
            'title': 'Evening Yoga',
            'recurring': True
        },
        {
            'day': 'Friday',
            'weekday': 4,
            'time': '9:00 AM',
            'time_obj': datetime.strptime('9:00 AM', '%I:%M %p').time(),
            'title': 'Morning Yoga',
            'recurring': True
        },
        {
            'day': 'Saturday',
            'weekday': 5,
            'time': '10:00 AM',
            'time_obj': datetime.strptime('10:00 AM', '%I:%M %p').time(),
            'title': 'Weekend Yoga',
            'recurring': True
        }
    ]
    
    return sample_events

def main():
    """Main function"""
    
    # print("="*70)
    print("Double Iris Yoga and Massage Schedule Scraper")
    # print("="*70)
    print()
    
    driver = None
    
    try:
        # Ask about browser visibility
        print("Options:")
        print("1. Run in background (headless)")
        print("2. Show browser window (for debugging)")
        
        choice = input("\nChoose option (1 or 2, default=1): ").strip() or "1"
        headless = (choice == '1')
        
        # Setup driver
        print("\n# Setting up Chrome WebDriver...")
        driver = setup_driver(headless=headless)
        
        # Scrape schedule
        events, page_content = scrape_schedule(driver)
        
        # Check if we found events
        if not events:
            print("\n" + "="*70)
            print("⚠️  No schedule items were automatically detected")
            # print("="*70)
            print("\nThe schedule page may use:")
            print("  - An embedded booking widget (like MindBody, Acuity, etc.)")
            print("  - A third-party scheduling system")
            print("  - Images or PDF schedule")
            print()
            print("Page content sample:")
            print("-" * 70)
            print(page_content[:500])
            print("-" * 70)
            print()
            
            use_sample = input("Create sample schedule based on typical yoga studio hours? (y/n): ").strip().lower()
            
            if use_sample == 'y':
                events = create_sample_schedule()
            else:
                print("\nTo manually extract the schedule:")
                print("1. Visit https://www.doubleirisyogaandmassage.com/schedule")
                print("2. Note the class times and days")
                print("3. Edit this script's create_sample_schedule() function")
                print("4. Re-run the script")
                return
        
        # Create ICS file
        if events:
            output_file = "double_iris_yoga_schedule.ics"
            print(f"\nCreating ICS file: {output_file}")
            print(f"Generating 12 weeks of recurring classes...")
            
            create_ics_file(events, output_file)
            
            # Summary
            print("\n" + "="*70)
            print("✓ ICS FILE CREATED!")
            # print("="*70)
            print(f"  Output: {output_file}")
            print(f"  Weekly classes: {len(events)}")
            print(f"  Total occurrences: {len(events) * 12}")
            print()
            print("Classes scheduled:")
            print("-" * 70)
            for event in sorted(events, key=lambda x: (x['weekday'], x['time'])):
                print(f"  {event['day']:12s} {event['time']:10s} - {event['title']}")
            print("-" * 70)
            print("\nYou can import this file into:")
            print("  • Google Calendar")
            print("  • Apple Calendar")
            print("  • Microsoft Outlook")
            print(f"\n{'='*70}\n")
        
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
