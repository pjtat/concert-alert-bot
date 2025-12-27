#!/usr/bin/env python3
"""
Concert Alert Bot
Monitors upcoming concerts for your favorite Spotify artists in your area.
"""

import json
import os
import time
import warnings
from datetime import datetime, timedelta
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import config

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')


class ConcertBot:
    def __init__(self):
        self.spotify = None  # Lazy initialization
        self.notified_concerts = self._load_notified_concerts()

    def _init_spotify(self):
        """Initialize Spotify client with OAuth (lazy)."""
        if self.spotify is None:
            self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
                redirect_uri=config.SPOTIFY_REDIRECT_URI,
                scope=config.SPOTIFY_SCOPES
            ))
        return self.spotify

    def _load_notified_concerts(self):
        """Load previously notified concerts from file."""
        if os.path.exists(config.NOTIFIED_CONCERTS_FILE):
            with open(config.NOTIFIED_CONCERTS_FILE, 'r') as f:
                return json.load(f)
        return []

    def _save_notified_concerts(self):
        """Save notified concerts to file."""
        with open(config.NOTIFIED_CONCERTS_FILE, 'w') as f:
            json.dump(self.notified_concerts, f, indent=2)

    def _load_curated_artists(self):
        """Load artists from manually curated text file."""
        artists = []
        with open(config.MY_ARTISTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    artists.append({
                        'name': line,
                        'id': None,  # We don't need Spotify ID for Ticketmaster search
                        'source': 'manual'
                    })
        return artists

    def get_favorite_artists(self):
        """Get user's curated artists merged with Spotify followed artists."""
        artists = []

        # Load curated artist list
        if os.path.exists(config.MY_ARTISTS_FILE):
            print(f"Loading curated artist list from {config.MY_ARTISTS_FILE}...")
            curated_artists = self._load_curated_artists()
            artists.extend(curated_artists)
            print(f"Loaded {len(curated_artists)} curated artists")

        # Also fetch followed artists from Spotify to catch any new additions
        print("Checking Spotify for followed artists...")
        self._init_spotify()

        followed = self.spotify.current_user_followed_artists(limit=50)
        spotify_count = 0
        for item in followed['artists']['items']:
            # Add if not already in list (case-insensitive comparison)
            if not any(a['name'].lower() == item['name'].lower() for a in artists):
                artists.append({
                    'name': item['name'],
                    'id': item['id'],
                    'source': 'spotify_followed'
                })
                spotify_count += 1

        # Handle pagination for followed artists
        while followed['artists']['next']:
            followed = self.spotify.next(followed['artists'])
            for item in followed['artists']['items']:
                if not any(a['name'].lower() == item['name'].lower() for a in artists):
                    artists.append({
                        'name': item['name'],
                        'id': item['id'],
                        'source': 'spotify_followed'
                    })
                    spotify_count += 1

        if spotify_count > 0:
            print(f"Added {spotify_count} new artists from Spotify follows")
        else:
            print("No new artists found on Spotify")

        print(f"Monitoring {len(artists)} artists total")

        # Cache artists
        with open(config.ARTISTS_CACHE_FILE, 'w') as f:
            json.dump(artists, f, indent=2)

        return artists

    def search_concerts(self, artist_name):
        """Search for concerts by artist name using Ticketmaster API."""
        url = f"{config.TICKETMASTER_BASE_URL}/events.json"

        # Calculate date range
        start_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        end_date = (datetime.now() + timedelta(days=30 * config.SEARCH_WINDOW_MONTHS)).strftime('%Y-%m-%dT%H:%M:%SZ')

        params = {
            'apikey': config.TICKETMASTER_API_KEY,
            'keyword': artist_name,
            'latlong': f'{config.LATITUDE},{config.LONGITUDE}',
            'radius': config.SEARCH_RADIUS,
            'unit': 'miles',
            'classificationName': 'music',
            'startDateTime': start_date,
            'endDateTime': end_date,
            'sort': 'date,asc'
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Rate limiting: wait 0.5 seconds between requests
            time.sleep(0.5)

            if '_embedded' in data and 'events' in data['_embedded']:
                return data['_embedded']['events']
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error searching concerts for {artist_name}: {e}")
            # If rate limited, wait longer before next request
            if '429' in str(e):
                print("  Rate limited - waiting 5 seconds...")
                time.sleep(5)
            return []

    def is_concert_notified(self, event_id):
        """Check if concert has already been notified."""
        return event_id in self.notified_concerts

    def add_notified_concert(self, event_id):
        """Add concert to notified list."""
        if event_id not in self.notified_concerts:
            self.notified_concerts.append(event_id)

    def is_tribute_show(self, event):
        """Check if event is a tribute band/cover show."""
        event_name = event.get('name', '').lower()

        # Keywords that indicate tribute/cover shows
        tribute_keywords = [
            'tribute', 'tributes', 'cover', 'covers',
            'experience', 'reimagined', 'celebration',
            'vs.', 'vs ', 'night with dj', 'starring'
        ]

        for keyword in tribute_keywords:
            if keyword in event_name:
                return True

        return False

    def is_artist_match(self, event, search_artist):
        """Verify the performing artist matches the search query."""
        search_lower = search_artist.lower()

        # Check if attractions (performers) data exists
        if '_embedded' not in event or 'attractions' not in event['_embedded']:
            # No performer data, fall back to name matching
            event_name = event.get('name', '').lower()
            return search_lower in event_name

        # Check actual performers
        for attraction in event['_embedded']['attractions']:
            attraction_name = attraction.get('name', '').lower()

            # Exact match or very close match
            if search_lower == attraction_name:
                return True

            # Handle cases like "The Weeknd" vs "Weeknd"
            if search_lower.replace('the ', '') == attraction_name.replace('the ', ''):
                return True

        return False

    def format_concert_alert(self, artist_name, event):
        """Format concert information for notification."""
        event_name = event.get('name', 'N/A')
        event_date = event.get('dates', {}).get('start', {}).get('localDate', 'N/A')
        event_time = event.get('dates', {}).get('start', {}).get('localTime', 'N/A')
        venue = event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'N/A')
        city = event.get('_embedded', {}).get('venues', [{}])[0].get('city', {}).get('name', 'N/A')
        url = event.get('url', 'N/A')

        alert = f"""
{'='*80}
🎵 NEW CONCERT ALERT!
{'='*80}
Artist: {artist_name}
Event: {event_name}
Date: {event_date} at {event_time}
Venue: {venue}, {city}
Tickets: {url}
{'='*80}
"""
        return alert

    def run(self):
        """Main execution function."""
        print("Starting Concert Alert Bot...")
        print(f"Searching for concerts within {config.SEARCH_RADIUS} miles of Los Angeles (lat/long: {config.LATITUDE},{config.LONGITUDE})")
        print()

        # Get artists
        artists = self.get_favorite_artists()

        new_concerts = []

        # Search for concerts
        print("\nSearching for concerts...")
        for i, artist in enumerate(artists, 1):
            print(f"[{i}/{len(artists)}] Checking {artist['name']}...")

            events = self.search_concerts(artist['name'])

            for event in events:
                event_id = event.get('id')

                # Skip if already notified
                if self.is_concert_notified(event_id):
                    continue

                # Filter out tribute shows
                if self.is_tribute_show(event):
                    continue

                # Verify artist match
                if not self.is_artist_match(event, artist['name']):
                    continue

                # This is a valid concert!
                alert = self.format_concert_alert(artist['name'], event)
                new_concerts.append(alert)
                self.add_notified_concert(event_id)
                print(f"  ✓ Found new concert: {event.get('name')}")

        # Write alerts to file
        if new_concerts:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(config.OUTPUT_FILE, 'a') as f:
                f.write(f"\n\nRun at: {timestamp}\n")
                f.write(f"Found {len(new_concerts)} new concert(s)\n")
                for alert in new_concerts:
                    f.write(alert)

            print(f"\n✅ Found {len(new_concerts)} new concert(s)! Check {config.OUTPUT_FILE}")
        else:
            print("\n📭 No new concerts found.")

        # Save notified concerts
        self._save_notified_concerts()
        print("\n✅ Done!")


if __name__ == '__main__':
    bot = ConcertBot()
    bot.run()
