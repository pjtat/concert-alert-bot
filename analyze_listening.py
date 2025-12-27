#!/usr/bin/env python3
"""
Analyze Spotify listening data and filter artists by listening frequency
"""

import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

def get_top_artists_all_ranges(spotify):
    """Get top artists across all time ranges with rankings"""
    artist_scores = {}

    # Weight: short_term (last 4 weeks) gets highest weight
    # medium_term (last 6 months) gets medium weight
    # long_term (several years) gets lowest weight
    time_ranges = {
        'short_term': 3,    # Last 4 weeks - most important
        'medium_term': 2,   # Last 6 months
        'long_term': 1      # All time
    }

    print("Analyzing your listening habits across different time periods...\n")

    for time_range, weight in time_ranges.items():
        print(f"Fetching {time_range.replace('_', ' ')} data...")
        top = spotify.current_user_top_artists(limit=50, time_range=time_range)

        for idx, item in enumerate(top['items']):
            artist_name = item['name']
            # Higher rank (lower index) = higher score
            rank_score = (50 - idx) * weight

            if artist_name in artist_scores:
                artist_scores[artist_name]['score'] += rank_score
                artist_scores[artist_name]['appearances'] += 1
                artist_scores[artist_name]['time_ranges'].append(time_range)
            else:
                artist_scores[artist_name] = {
                    'score': rank_score,
                    'appearances': 1,
                    'time_ranges': [time_range],
                    'id': item['id']
                }

    return artist_scores

def filter_by_listening(min_score=None, top_n=None, require_recent=False):
    """Filter artists based on listening data"""

    # Initialize Spotify
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
        scope=config.SPOTIFY_SCOPES
    ))

    # Get listening data
    artist_scores = get_top_artists_all_ranges(spotify)

    # Load current artist list
    with open('my_artists.txt', 'r') as f:
        current_artists = [line.strip() for line in f if line.strip()]

    # Filter and score
    filtered_artists = []

    for artist in current_artists:
        if artist in artist_scores:
            score_data = artist_scores[artist]

            # Apply filters
            if require_recent and 'short_term' not in score_data['time_ranges']:
                continue  # Skip if not in recent listening

            if min_score and score_data['score'] < min_score:
                continue  # Skip if score too low

            filtered_artists.append({
                'name': artist,
                'score': score_data['score'],
                'appearances': score_data['appearances'],
                'time_ranges': score_data['time_ranges']
            })

    # Sort by score (highest first)
    filtered_artists.sort(key=lambda x: x['score'], reverse=True)

    # Apply top_n filter if specified
    if top_n:
        filtered_artists = filtered_artists[:top_n]

    return filtered_artists, current_artists, artist_scores

def show_analysis():
    """Show listening analysis and recommendations"""
    print("=" * 80)
    print("SPOTIFY LISTENING ANALYSIS")
    print("=" * 80)
    print()

    filtered, current, all_scores = filter_by_listening()

    print(f"Total artists in your list: {len(current)}")
    print(f"Artists you actually listen to: {len(filtered)}")
    print(f"Artists you don't listen to: {len(current) - len(filtered)}")
    print()

    # Show top listeners
    print("=" * 80)
    print("YOUR TOP 50 MOST LISTENED ARTISTS (from your list)")
    print("=" * 80)
    for i, artist in enumerate(filtered[:50], 1):
        ranges = ', '.join(artist['time_ranges'])
        print(f"{i:2}. {artist['name']:<40} Score: {artist['score']:>4}  ({ranges})")

    print("\n" + "=" * 80)
    print("FILTER OPTIONS")
    print("=" * 80)
    print("1. Keep only artists you actually listen to")
    print("2. Keep only top 100 most listened")
    print("3. Keep only top 200 most listened")
    print("4. Keep only artists you've listened to in last 4 weeks")
    print("5. Keep only artists you've listened to in last 6 months")
    print("6. Show artists you follow but never listen to")
    print("7. Exit without changes")

    return filtered, current, all_scores

if __name__ == '__main__':
    filtered, current, all_scores = show_analysis()

    choice = input("\nEnter your choice (1-7): ").strip()

    if choice == '1':
        # Keep only artists you listen to
        artists_to_keep = [a['name'] for a in filtered]
    elif choice == '2':
        # Top 100
        artists_to_keep = [a['name'] for a in filtered[:100]]
    elif choice == '3':
        # Top 200
        artists_to_keep = [a['name'] for a in filtered[:200]]
    elif choice == '4':
        # Recent (last 4 weeks)
        artists_to_keep = [a['name'] for a in filtered if 'short_term' in a['time_ranges']]
    elif choice == '5':
        # Last 6 months
        artists_to_keep = [a['name'] for a in filtered if 'short_term' in a['time_ranges'] or 'medium_term' in a['time_ranges']]
    elif choice == '6':
        # Show artists you follow but don't listen to
        not_listened = [a for a in current if a not in all_scores]
        print(f"\n{len(not_listened)} artists you follow but don't listen to:")
        for artist in sorted(not_listened)[:50]:
            print(f"  - {artist}")
        print("\nNo changes made to my_artists.txt")
        exit(0)
    else:
        print("No changes made.")
        exit(0)

    # Save filtered list
    with open('my_artists.txt', 'w') as f:
        for artist in sorted(artists_to_keep):
            f.write(f"{artist}\n")

    print(f"\n✓ Updated my_artists.txt")
    print(f"  Before: {len(current)} artists")
    print(f"  After: {len(artists_to_keep)} artists")
    print(f"  Removed: {len(current) - len(artists_to_keep)} artists")
