#!/usr/bin/env python3
"""
compare_ics.py - Compare two ICS files, ignoring DTSTAMP lines and past events.

Usage: python3 compare_ics.py file1.ics file2.ics

Prints "changed" if future events differ, "not changed" if they are the same.

Past events are excluded: an event is considered past if DTSTART date is before
today AND DTEND is either empty or also before today.
"""

import sys
import os
from datetime import date, datetime


def parse_date(value):
    """Parse a DTSTART or DTEND value into a date, ignoring the time portion.
    Returns None if the value is empty or unparseable."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    # Strip timezone suffix if present (e.g. 20260521T133000Z -> 20260521)
    date_part = value.split('T')[0]
    try:
        return datetime.strptime(date_part, '%Y%m%d').date()
    except ValueError:
        return None


def get_field_value(line, field):
    """Extract the value from a line like 'DTSTART:20260521T133000Z'.
    Also handles parameterised forms like 'DTSTART;TZID=America/New_York:20260521T093000'."""
    if line.startswith(field + ':'):
        return line[len(field) + 1:]
    if line.startswith(field + ';'):
        # Value follows the last colon
        return line.split(':', 1)[1] if ':' in line else None
    return None


def is_past_event(block, today):
    """Return True if the event block should be treated as a past event."""
    dtstart = None
    dtend = None

    for line in block:
        val = get_field_value(line, 'DTSTART')
        if val is not None:
            dtstart = parse_date(val)
        val = get_field_value(line, 'DTEND')
        if val is not None:
            dtend = parse_date(val)

    if dtstart is None:
        return False  # Can't determine; keep the event

    if dtstart < today:
        # Past only if DTEND is also absent/past
        if dtend is None or dtend < today:
            return True

    return False


def load_future_events(filename):
    """Parse an ICS file and return a set of VEVENT blocks (as tuples of lines),
    with DTSTAMP lines removed and past events excluded."""
    today = date.today()

    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\r\n') for line in f]

    future_events = set()
    in_vevent = False
    current_block = []

    for line in lines:
        if line == 'BEGIN:VEVENT':
            in_vevent = True
            current_block = [line]
        elif line == 'END:VEVENT':
            current_block.append(line)
            in_vevent = False

            if not is_past_event(current_block, today):
                # Strip DTSTAMP lines before storing
                filtered = tuple(
                    l for l in current_block
                    if not l.startswith('DTSTAMP:')
                )
                future_events.add(filtered)

            current_block = []
        elif in_vevent:
            current_block.append(line)

    return future_events


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} file1.ics file2.ics", file=sys.stderr)
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]

    try:
        events1 = load_future_events(file1)
    except FileNotFoundError:
        print(f"Error: file not found: {file1}", file=sys.stderr)
        sys.exit(1)

    try:
        events2 = load_future_events(file2)
    except FileNotFoundError:
        print(f"Error: file not found: {file2}", file=sys.stderr)
        sys.exit(1)

    if events1 == events2:
        # os.environ['RESULT'] = 'not changed'
        print("not changed")
    else:
        # os.environ['RESULT'] = 'changed'
        print("changed")
        # Optional: show a summary of what differs
        only_in_1 = events1 - events2
        only_in_2 = events2 - events1
        if only_in_1:
            print(f"  Events only in {file1}: {len(only_in_1)}", file=sys.stderr)
            for ev in sorted(only_in_1):
                summary = next((l for l in ev if l.startswith('SUMMARY:')), '')
                dtstart = next((l for l in ev if l.startswith('DTSTART')), '')
                print(f"    {dtstart}  {summary}", file=sys.stderr)
        if only_in_2:
            print(f"  Events only in {file2}: {len(only_in_2)}", file=sys.stderr)
            for ev in sorted(only_in_2):
                summary = next((l for l in ev if l.startswith('SUMMARY:')), '')
                dtstart = next((l for l in ev if l.startswith('DTSTART')), '')
                print(f"    {dtstart}  {summary}", file=sys.stderr)


if __name__ == '__main__':
    main()