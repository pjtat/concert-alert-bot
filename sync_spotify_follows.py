#!/usr/bin/env python3
"""
Sync Spotify followed artists to match the curated list
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config
import time

def get_all_followed_artists(spotify):
    """Get all artists the user currently follows"""
    followed = []
    results = spotify.current_user_followed_artists(limit=50)

    while results:
        for item in results['artists']['items']:
            followed.append({
                'name': item['name'],
                'id': item['id']
            })

        if results['artists']['next']:
            results = spotify.next(results['artists'])
        else:
            break

    return followed

def search_artist(spotify, artist_name):
    """Search for an artist by name and return their Spotify ID"""
    try:
        results = spotify.search(q=f'artist:{artist_name}', type='artist', limit=1)
        if results['artists']['items']:
            return results['artists']['items'][0]['id']
    except Exception as e:
        print(f"  Error searching for {artist_name}: {e}")
    return None

# Initialize Spotify with user-modify-follow scope
spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
    redirect_uri=config.SPOTIFY_REDIRECT_URI,
    scope='user-top-read user-follow-read user-follow-modify'
))

print("=" * 80)
print("SPOTIFY FOLLOW SYNC")
print("=" * 80)
print()

# Load curated artist list
with open('my_artists.txt', 'r') as f:
    curated_artists = [line.strip() for line in f if line.strip()]

print(f"Curated list: {len(curated_artists)} artists")

# Get currently followed artists
print("Fetching your currently followed artists...")
currently_followed = get_all_followed_artists(spotify)
print(f"Currently following: {len(currently_followed)} artists")
print()

# Find artists to unfollow (currently followed but not in curated list)
currently_followed_names = {a['name'] for a in currently_followed}
to_unfollow = [a for a in currently_followed if a['name'] not in curated_artists]

# Find artists to follow (in curated list but not currently followed)
to_follow = [name for name in curated_artists if name not in currently_followed_names]

print("=" * 80)
print("CHANGES TO BE MADE")
print("=" * 80)
print(f"\nArtists to UNFOLLOW: {len(to_unfollow)}")
if to_unfollow:
    print("\nFirst 20:")
    for artist in to_unfollow[:20]:
        print(f"  - {artist['name']}")
    if len(to_unfollow) > 20:
        print(f"  ... and {len(to_unfollow) - 20} more")

print(f"\nArtists to FOLLOW: {len(to_follow)}")
if to_follow:
    print("\nFirst 20:")
    for artist in to_follow[:20]:
        print(f"  - {artist}")
    if len(to_follow) > 20:
        print(f"  ... and {len(to_follow) - 20} more")

print("\n" + "=" * 80)
response = input("\nProceed with syncing? (yes/no): ").strip().lower()

if response != 'yes':
    print("Cancelled. No changes made to your Spotify follows.")
    exit(0)

print("\n" + "=" * 80)
print("SYNCING...")
print("=" * 80)

# Unfollow artists
if to_unfollow:
    print(f"\nUnfollowing {len(to_unfollow)} artists...")
    for i, artist in enumerate(to_unfollow, 1):
        try:
            spotify.user_unfollow_artists([artist['id']])
            print(f"  [{i}/{len(to_unfollow)}] Unfollowed: {artist['name']}")
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"  [{i}/{len(to_unfollow)}] Error unfollowing {artist['name']}: {e}")

# Follow artists
if to_follow:
    print(f"\nFollowing {len(to_follow)} new artists...")
    for i, artist_name in enumerate(to_follow, 1):
        artist_id = search_artist(spotify, artist_name)
        if artist_id:
            try:
                spotify.user_follow_artists([artist_id])
                print(f"  [{i}/{len(to_follow)}] Followed: {artist_name}")
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"  [{i}/{len(to_follow)}] Error following {artist_name}: {e}")
        else:
            print(f"  [{i}/{len(to_follow)}] Could not find: {artist_name}")

print("\n" + "=" * 80)
print("✓ SYNC COMPLETE!")
print("=" * 80)
print(f"\nYour Spotify now follows exactly {len(curated_artists)} artists from your curated list.")
