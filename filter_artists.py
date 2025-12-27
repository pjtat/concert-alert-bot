#!/usr/bin/env python3
"""
Filter out deceased artists and artists who haven't toured in years
"""

# Artists to remove (deceased or haven't toured in many years)
ARTISTS_TO_REMOVE = {
    "2Pac",
    "Aretha Franklin",
    "Big Pun",
    "Bill Withers",
    "Billie Holiday",
    "Billy Paul",
    "Bob Marley & The Wailers",
    "Chuck Berry",
    "Curtis Mayfield",
    "Darondo",
    "David Bowie",
    "Dobie Gray",
    "Dusty Springfield",
    "Eazy-E",
    "Elliott Smith",
    "Frank Sinatra",
    "George Harrison",
    "George Michael",
    "Glen Campbell",
    "Gordon Lightfoot",
    "Grateful Dead",
    "Idris Muhammad",
    "James Brown",
    "Janis Joplin",
    "Jeff Buckley",
    "Jimi Hendrix",
    "Jim Croce",
    "Johann Sebastian Bach",
    "Johnny Bristol",
    "Johnny Cash",
    "Joy Division",
    "Juice WRLD",
    "Led Zeppelin",
    "Leon Ware",
    "Lou Reed",
    "Lou Rawls",
    "Mac Miller",
    "Madvillain",
    "Marlena Shaw",
    "Marty Robbins",
    "Marvin Gaye",
    "Merle Haggard",
    "MF DOOM",
    "Michael Jackson",
    "Miles Davis",
    "Nirvana",
    "Nico",
    "Nina Simone",
    "Ol' Dirty Bastard",
    "Otis Redding",
    "Pop Smoke",
    "Prince",
    "Rick James",
    "Sam Cooke",
    "Selena",
    "Stevie Ray Vaughan",
    "T. Rex",
    "Teddy Pendergrass",
    "The Beatles",
    "The Notorious B.I.G.",
    "Tom Petty",
    "Tom Petty and the Heartbreakers",
    "Tyrone Davis",
    "XXXTENTACION",
    "Yvonne Fair",
    # Bands that haven't toured in many years
    "Beastie Boys",
    "Cream",
    "Daft Punk",
    "Fugazi",
    "N.W.A.",
    "Ramones",
    "Soundgarden",
    "The Clash",
    "The Doors",
    "The Mamas & The Papas",
    "The Velvet Underground",
    "UGK",
}

def filter_artists(input_file, output_file):
    """Read artists, filter out deceased/inactive, write back"""
    with open(input_file, 'r') as f:
        artists = [line.strip() for line in f if line.strip()]

    # Filter out deceased/inactive artists
    filtered = [a for a in artists if a not in ARTISTS_TO_REMOVE]

    removed_count = len(artists) - len(filtered)

    # Write back
    with open(output_file, 'w') as f:
        for artist in filtered:
            f.write(f"{artist}\n")

    print(f"Original count: {len(artists)}")
    print(f"Removed: {removed_count}")
    print(f"Remaining: {len(filtered)}")
    print(f"\nRemoved artists:")
    for artist in sorted(ARTISTS_TO_REMOVE & set(artists)):
        print(f"  - {artist}")

if __name__ == '__main__':
    filter_artists('my_artists.txt', 'my_artists.txt')
