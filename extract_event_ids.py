#!/usr/bin/env python3
"""
Extract event IDs from concert alert URLs
"""

import re
import json
from datetime import datetime

def extract_event_id_from_url(url):
    """Extract event ID from Ticketmaster/Ticketweb URL."""
    # Ticketmaster pattern: /event/EVENTID or ending with /event/EVENTID
    tm_match = re.search(r'/event/([A-Za-z0-9_-]+)$', url)
    if tm_match:
        return tm_match.group(1)

    # Ticketweb pattern: ends with number like /14645493
    tw_match = re.search(r'/(\d+)$', url)
    if tw_match:
        return tw_match.group(1)

    return None

def parse_concert_alerts(filename='concert_alerts.txt'):
    """Parse concert_alerts.txt and extract event IDs with dates."""
    events = {}

    with open(filename, 'r') as f:
        content = f.read()

    # Split by concert alert blocks
    alert_blocks = content.split('=' * 80)

    for block in alert_blocks:
        if 'Tickets: ' in block and 'Date: ' in block:
            # Extract URL
            url_match = re.search(r'Tickets: (https?://[^\s]+)', block)
            # Extract date
            date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', block)

            if url_match and date_match:
                url = url_match.group(1)
                date = date_match.group(1)
                event_id = extract_event_id_from_url(url)

                if event_id:
                    events[event_id] = date

    return events

def main():
    print("Extracting event IDs from concert_alerts.txt...")
    events = parse_concert_alerts()

    print(f"\nFound {len(events)} unique events")
    print("\nEvent IDs with dates:")
    for event_id, date in sorted(events.items(), key=lambda x: x[1]):
        print(f"  {event_id}: {date}")

    # Load current tracking file
    try:
        with open('notified_concerts.json', 'r') as f:
            existing = json.load(f)
            # Convert old format (list) to new format (dict)
            if isinstance(existing, list):
                existing = {eid: None for eid in existing}
    except FileNotFoundError:
        existing = {}

    print(f"\nCurrently tracking: {len(existing)} events")

    # Merge with new events
    new_events = 0
    for event_id, date in events.items():
        if event_id not in existing:
            existing[event_id] = date
            new_events += 1

    print(f"Adding {new_events} new events to tracking")

    # Save updated tracking file
    with open('notified_concerts.json', 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"\n✅ Updated notified_concerts.json with {len(existing)} total events")

if __name__ == '__main__':
    main()
