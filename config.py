import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'

# Ticketmaster Configuration
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY')
TICKETMASTER_BASE_URL = 'https://app.ticketmaster.com/discovery/v2'

# Location Configuration (Los Angeles)
LATITUDE = float(os.getenv('LATITUDE', '34.0522'))
LONGITUDE = float(os.getenv('LONGITUDE', '-118.2437'))
SEARCH_RADIUS = int(os.getenv('SEARCH_RADIUS', '40'))  # in miles

# Data Files
MY_ARTISTS_FILE = 'my_artists.txt'  # Manual curated list (takes priority)
ARTISTS_CACHE_FILE = 'artists_cache.json'
NOTIFIED_CONCERTS_FILE = 'notified_concerts.json'
OUTPUT_FILE = 'concert_alerts.txt'

# Spotify Scopes
SPOTIFY_SCOPES = 'user-top-read user-follow-read'

# How far ahead to look for concerts (in months)
SEARCH_WINDOW_MONTHS = 12

# SendGrid Email Configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # Must be verified in SendGrid
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
SEND_EMAIL_NOTIFICATIONS = os.getenv('SEND_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'

# Skip Spotify (useful for GitHub Actions where OAuth doesn't work)
SKIP_SPOTIFY = os.getenv('SKIP_SPOTIFY', 'false').lower() == 'true'
