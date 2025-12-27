#!/usr/bin/env python3
"""
Organize artists: listened-to artists at top, others below for review
"""

import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

def get_top_artists_all_ranges(spotify):
    """Get top artists across all time ranges"""
    artist_scores = {}

    time_ranges = {
        'short_term': 3,
        'medium_term': 2,
        'long_term': 1
    }

    for time_range, weight in time_ranges.items():
        top = spotify.current_user_top_artists(limit=50, time_range=time_range)
        for idx, item in enumerate(top['items']):
            artist_name = item['name']
            rank_score = (50 - idx) * weight

            if artist_name in artist_scores:
                artist_scores[artist_name]['score'] += rank_score
            else:
                artist_scores[artist_name] = {'score': rank_score}

    return artist_scores

# Initialize Spotify
spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
    redirect_uri=config.SPOTIFY_REDIRECT_URI,
    scope=config.SPOTIFY_SCOPES
))

print("Fetching your listening data...")
artist_scores = get_top_artists_all_ranges(spotify)

# Load current artist list
with open('my_artists.txt', 'r') as f:
    current_artists = [line.strip() for line in f if line.strip()]

# Separate into listened-to and not-listened-to
listened_to = []
not_listened_to = []

for artist in current_artists:
    if artist in artist_scores:
        listened_to.append((artist, artist_scores[artist]['score']))
    else:
        not_listened_to.append(artist)

# Sort listened-to by score (highest first)
listened_to.sort(key=lambda x: x[1], reverse=True)
listened_to_names = [name for name, score in listened_to]

# Keep not-listened-to alphabetically sorted
not_listened_to.sort()

# Write reorganized file
with open('my_artists.txt', 'w') as f:
    f.write("# ========================================\n")
    f.write("# ARTISTS YOU ACTUALLY LISTEN TO (65)\n")
    f.write("# Sorted by listening frequency\n")
    f.write("# ========================================\n")
    for artist in listened_to_names:
        f.write(f"{artist}\n")

    f.write("\n")
    f.write("# ========================================\n")
    f.write("# ARTISTS TO REVIEW (565)\n")
    f.write("# You follow these but rarely/never listen\n")
    f.write("# Delete the ones you don't want alerts for\n")
    f.write("# ========================================\n")
    for artist in not_listened_to:
        f.write(f"{artist}\n")

print(f"✓ Reorganized my_artists.txt")
print(f"  - Top section: {len(listened_to_names)} artists you listen to")
print(f"  - Bottom section: {len(not_listened_to)} artists to review")
print(f"\nOpen my_artists.txt and delete any artists from the bottom section you don't want!")
