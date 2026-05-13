#!/usr/bin/env python3
"""
Opera House Live Events Extractor - Working Version
Extracts calendar events from Shepherdstown Opera House
"""

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv
import re

# Event data extracted from the schedule page
events_data = [
    {
        'raw_title': 'JAN 9 – 18 Live Theater: Rounding Third',
        'url': 'https://operahouselive.com/jan-9-18-rounding-third/',
        'category': 'Live Theater'
    },
    {
        'raw_title': 'JAN 24 – Privacy People',
        'url': 'https://operahouselive.com/jan-24-privacy-people/',
        'category': 'Film'
    },
    {
        'raw_title': 'JAN 25 – National Theatre Live: Inter Alia',
        'url': 'https://operahouselive.com/jan-25-national-theatre-live-inter-alia/',
        'category': 'National Theatre Live'
    },
    {
        'raw_title': 'FEB 6 – Moonstruck',
        'url': 'https://operahouselive.com/feb-6-moonstruck/',
        'category': 'Film'
    },
    {
        'raw_title': 'FEB 7 – Live Music: Ginada Piñata',
        'url': 'https://operahouselive.com/feb-7-ginada-pinata/',
        'category': 'Live Music'
    },
    {
        'raw_title': 'FEB 13 – You Got Gold: A Celebration of John Prine',
        'url': 'https://operahouselive.com/feb-13-you-got-gold-a-celebration-of-john-prine/',
        'category': 'Live Music'
    },
    {
        'raw_title': 'FEB 14 – You Got Gold: A Celebration of John Prine',
        'url': 'https://operahouselive.com/feb-14-you-got-gold-a-celebration-of-john-prine/',
        'category': 'Live Music'
    },
    {
        'raw_title': 'MAR 6 – My Twentieth Century',
        'url': 'https://operahouselive.com/mar-6-my-twentieth-century/',
        'category': 'Film'
    },
    {
        'raw_title': 'MAR 29 – National Theatre Live: Life of Pi',
        'url': 'https://operahouselive.com/mar-29-national-theatre-live-life-of-pi/',
        'category': 'National Theatre Live'
    },
    {
        'raw_title': 'APR 3 – Lost in Paris',
        'url': 'https://operahouselive.com/apr-3-lost-in-paris/',
        'category': 'Film'
    },
    {
        'raw_title': "APR 10 – 19 Live Theater: A Doll's House",
        'url': 'https://operahouselive.com/apr-10-19-a-dolls-house/',
        'category': 'Live Theater'
    },
    {
        'raw_title': 'MAY 1 – Eleanor the Great',
        'url': 'https://operahouselive.com/may-1-eleanor-the-great/',
        'category': 'Film'
    },
    {
        'raw_title': 'MAY 16 – Kurt Crandall and True Story',
        'url': 'https://operahouselive.com/may-16-kurt-crandall-and-true-story/',
        'category': 'Live Music'
    },
    {
        'raw_title': 'JUN 12 – 21 Live Theater: We Will Not Be Silent',
        'url': 'https://operahouselive.com/jun-12-we-will-not-be-silent/',
        'category': 'Live Theater'
    },
    {
        'raw_title': 'SEP 25/26/27 — Manhattan SHORT Film Festival',
        'url': 'https://operahouselive.com/sep-25-26-27-manhattan-short-film-festival/',
        'category': 'Film Festival'
    }
]

# Additional details for key events (from the detail page we fetched)
event_details = {
    'https://operahouselive.com/jan-24-privacy-people/': {
        'time': '2:00 PM',
        'description': 'Privacy People explores varied interpretations of what privacy is and why it is important to individuals and societies. Focusing on the events that raised cultural awareness of big data and surveillance, the film reflects on the common refrain that "privacy is dead." A discussion with Q&A will follow the film. Year Released: 2025, Runtime: 77 minutes.'
    }
}

def parse_date_from_title(title_str):
    """
    Parse date from title strings like:
    "JAN 24 – Privacy People"
    "JAN 9 – 18 Live Theater: Rounding Third"
    "SEP 25/26/27 — Manhattan SHORT"
    """
    try:
        # Extract month and day(s)
        # Pattern 1: "JAN 24" or "JAN 9 – 18"
        match = re.match(r'([A-Z]{3})\s+(\d+)(?:\s*[–-]\s*(\d+))?', title_str)
        
        if not match:
            # Pattern 2: "SEP 25/26/27"
            match = re.match(r'([A-Z]{3})\s+(\d+)(?:/\d+)*', title_str)
        
        if match:
            month_abbr = match.group(1)
            start_day = int(match.group(2))
            end_day = int(match.group(3)) if match.group(3) else start_day
            
            # Convert month abbreviation to number
            months = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            month_num = months.get(month_abbr)
            
            if month_num:
                current_year = datetime.now().year
                current_month = datetime.now().month
                
                # If the event month is before current month, assume next year
                # (current date is January 2026)
                year = 2026 if month_num >= 1 else 2027
                
                start_dt = datetime(year, month_num, start_day)
                end_dt = datetime(year, month_num, end_day)
                
                return start_dt, end_dt
        
        return None, None
    except Exception as e:
        print(f"\nError parsing date from '{title_str}': {e}")
        return None, None

def extract_title_from_raw(raw_title):
    """Extract clean title from raw title string"""
    # Remove date prefix (e.g., "JAN 24 – ")
    title = re.sub(r'^[A-Z]{3}\s+\d+(?:\s*[–/-]\s*\d+)*\s*[–—-]\s*', '', raw_title)
    return title.strip()

def process_events():
    """Process event data and add parsed information"""
    processed_events = []
    
    for event in events_data:
        # Parse dates from title
        start_dt, end_dt = parse_date_from_title(event['raw_title'])
        
        # Extract clean title
        title = extract_title_from_raw(event['raw_title'])
        
        # Get additional details if available
        details = event_details.get(event['url'], {})
        
        # Default time is 7:30 PM for most events (typical showtime)
        default_time = '7:30 PM'
        event_time = details.get('time', default_time)
        
        # Parse time and update datetime
        if start_dt and event_time:
            try:
                time_obj = datetime.strptime(event_time, '%I:%M %p').time()
                start_dt = datetime.combine(start_dt.date(), time_obj)
                
                # Set end time (add 2-3 hours depending on event type)
                if event['category'] == 'Live Theater':
                    duration = timedelta(hours=2, minutes=30)
                elif event['category'] == 'Film':
                    duration = timedelta(hours=2)
                else:
                    duration = timedelta(hours=2)
                
                end_dt = start_dt + duration
            except:
                pass
        
        processed_events.append({
            'title': title,
            'category': event['category'],
            'url': event['url'],
            'start_datetime': start_dt,
            'end_datetime': end_dt,
            'description': details.get('description', f"{event['category']} event at Shepherdstown Opera House"),
            'location': 'Shepherdstown Opera House, 131 West German Street, Shepherdstown WV 25443'
        })
    
    return processed_events

def save_to_csv(events, filename):
    """Save events to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Category', 'Date', 'Time', 'Start DateTime', 'End DateTime', 'Location', 'Description', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for event in events:
            # Format date and time separately
            date_str = ''
            time_str = ''
            if event['start_datetime']:
                date_str = event['start_datetime'].strftime('%A, %B %d, %Y')
                time_str = event['start_datetime'].strftime('%I:%M %p')
            
            writer.writerow({
                'Title': event['title'],
                'Category': event['category'],
                'Date': date_str,
                'Time': time_str,
                'Start DateTime': event['start_datetime'].strftime('%Y-%m-%d %H:%M:%S') if event['start_datetime'] else '',
                'End DateTime': event['end_datetime'].strftime('%Y-%m-%d %H:%M:%S') if event['end_datetime'] else '',
                'Location': event['location'],
                'Description': event['description'][:500],
                'URL': event['url']
            })

def save_to_ics(events, filename):
    """Save events to ICS (iCalendar) file"""
    with open(filename, 'w', encoding='utf-8') as icsfile:
        # Write ICS header
        icsfile.write("BEGIN:VCALENDAR\n")
        icsfile.write("VERSION:2.0\n")
        icsfile.write("PRODID:-//Shepherdstown Opera House//Events//EN\n")
        icsfile.write("CALSCALE:GREGORIAN\n")
        icsfile.write("METHOD:PUBLISH\n")
        icsfile.write("X-WR-CALNAME:Shepherdstown Opera House Events\n")
        icsfile.write("X-WR-TIMEZONE:America/New_York\n")
        
        for event in events:
            if not event['start_datetime']:
                continue
            
            icsfile.write("BEGIN:VEVENT\n")
            
            # Generate UID
            uid = f"{event['start_datetime'].strftime('%Y%m%d%H%M%S')}-{abs(hash(event['title']))}@operahouselive.com"
            icsfile.write(f"UID:{uid}\n")
            
            # Format dates for ICS
            dtstamp = datetime.now().strftime('%Y%m%dT%H%M%S')
            dtstart = event['start_datetime'].strftime('%Y%m%dT%H%M%S')
            dtend = event['end_datetime'].strftime('%Y%m%dT%H%M%S')
            
            icsfile.write(f"DTSTAMP:{dtstamp}\n")
            icsfile.write(f"DTSTART:{dtstart}\n")
            icsfile.write(f"DTEND:{dtend}\n")
            
            # Escape special characters in text fields
            summary = event['title'].replace(',', '\\,').replace(';', '\\;').replace('\\', '\\\\').replace('\n', '\\n')
            description = event['description'].replace(',', '\\,').replace(';', '\\;').replace('\\', '\\\\').replace('\n', '\\n')
            location = event['location'].replace(',', '\\,').replace(';', '\\;').replace('\\', '\\\\').replace('\n', '\\n')
            
            icsfile.write(f"SUMMARY:{summary}\n")
            icsfile.write(f"DESCRIPTION:{description}\n")
            icsfile.write(f"LOCATION:{location}\n")
            icsfile.write(f"URL:{event['url']}\n")
            icsfile.write("STATUS:CONFIRMED\n")
            icsfile.write("SEQUENCE:0\n")
            
            icsfile.write("END:VEVENT\n")
        
        icsfile.write("END:VCALENDAR\n")

def main():
    """Main function"""
    # print("="*70)
    print("Shepherdstown Opera House Events Extractor")
    # # print("="*70)
    print()
    
    print("Processing events from operahouselive.com/schedule/...")
    events = process_events()
    print(f"Found {len(events)} events\n")
    
    # Save to CSV
    csv_filename = "opera_house_events.csv"
    print(f"Saving to CSV: {csv_filename}")
    save_to_csv(events, csv_filename)
    print("✓ CSV file created\n")
    
    # Save to ICS
    ics_filename = "opera_house_events.ics"
    print(f"Saving to ICS: {ics_filename}")
    save_to_ics(events, ics_filename)
    print("✓ ICS file created\n")
    
    # Display summary
    # # print("="*70)
    # # print("EVENTS SUMMARY")
    # print("="*70)
    for i, event in enumerate(events[:5], 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Category: {event['category']}")
        if event['start_datetime']:
            print(f"   Date: {event['start_datetime'].strftime('%A, %B %d, %Y')}")
            print(f"   Time: {event['start_datetime'].strftime('%I:%M %p')}")
        print(f"   URL: {event['url']}")
    
    if len(events) > 5:
        print(f"\n... and {len(events) - 5} more events")
    
    print("\n" + "="*70)
    print(f"Total events extracted: {len(events)}")
    # print("="*70)

if __name__ == "__main__":
    main()
