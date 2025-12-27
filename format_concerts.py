#!/usr/bin/env python3
"""
Format concert alerts into a more readable format
"""

import json
from datetime import datetime

# Read notified concerts to get event details
with open('notified_concerts.json', 'r') as f:
    event_ids = json.load(f)

# Parse the concert_alerts.txt file
concerts = []
current_concert = {}

with open('concert_alerts.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('Artist: '):
            current_concert['artist'] = line.replace('Artist: ', '')
        elif line.startswith('Event: '):
            current_concert['event'] = line.replace('Event: ', '')
        elif line.startswith('Date: '):
            date_str = line.replace('Date: ', '').split(' at ')
            current_concert['date'] = date_str[0]
            current_concert['time'] = date_str[1] if len(date_str) > 1 else ''
        elif line.startswith('Venue: '):
            current_concert['venue'] = line.replace('Venue: ', '')
        elif line.startswith('Tickets: '):
            current_concert['url'] = line.replace('Tickets: ', '')
            concerts.append(current_concert.copy())
            current_concert = {}

# Sort by date
concerts.sort(key=lambda x: x.get('date', ''))

# Count concerts per artist
artist_counts = {}
for concert in concerts:
    artist = concert['artist']
    artist_counts[artist] = artist_counts.get(artist, 0) + 1

# Sort artists alphabetically
sorted_artists = sorted(artist_counts.items())

# Write formatted output
with open('concert_alerts_formatted.txt', 'w') as f:
    f.write("=" * 100 + "\n")
    f.write(f"CONCERT ALERTS - {len(concerts)} SHOWS FOUND\n")
    f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    f.write("=" * 100 + "\n\n")

    # Artists with upcoming concerts
    f.write("ARTISTS WITH UPCOMING CONCERTS:\n")
    f.write("-" * 100 + "\n")
    for artist, count in sorted_artists:
        f.write(f"  {artist} ({count})\n")
    f.write("\n")

    # Group by month
    current_month = None
    for concert in concerts:
        # Parse date
        try:
            date_obj = datetime.strptime(concert['date'], '%Y-%m-%d')
            month_year = date_obj.strftime('%B %Y')
            formatted_date = date_obj.strftime('%a, %b %d, %Y')
        except:
            month_year = "TBD"
            formatted_date = concert['date']

        # Print month header
        if month_year != current_month:
            if current_month is not None:
                f.write("\n")
            f.write("-" * 100 + "\n")
            f.write(f"{month_year.upper()}\n")
            f.write("-" * 100 + "\n\n")
            current_month = month_year

        # Print concert in compact format
        f.write(f"{formatted_date} @ {concert.get('time', 'TBD')}\n")
        f.write(f"  {concert['artist']}\n")

        # Only show event name if different from artist name
        if concert['event'] != concert['artist']:
            f.write(f"  {concert['event']}\n")

        f.write(f"  {concert['venue']}\n")
        f.write(f"  {concert['url']}\n")
        f.write("\n")

    f.write("=" * 100 + "\n")
    f.write(f"Total: {len(concerts)} concerts\n")
    f.write("=" * 100 + "\n")

print(f"✓ Created concert_alerts_formatted.txt with {len(concerts)} concerts")
print(f"  Grouped by month and sorted by date")
