#!/usr/bin/env python3
"""
Categorize remaining artists into expected yes/no
"""

# Artists user kept above Nas (to move to confirmed)
ABOVE_NAS = [
    "A Tribe Called Quest",
    "A$AP Ferg",
    "A$AP Rocky",
    "Adele",
    "Adrianne Lenker",
    "Alanis Morissette",
    "Alex G",
    "Anderson .Paak",
    "André 3000",
    "Arcade Fire",
    "BALTHVS",
    "BROCKHAMPTON",
    "Barry Can't Swim",
    "Ben Quad",
    "Big Thief",
    "Big Wild",
    "BigXthaPlug",
    "Billy Joel",
    "Billy Strings",
    "Black Country, New Road",
    "Bleachers",
    "Bruce Springsteen",
    "Caamp",
    "Cage The Elephant",
    "Calvin Harris",
    "Cam'ron",
    "Cardi B",
    "Caribou",
    "Carly Cosgrove",
    "Carole King",
    "Caroline Polachek",
    "Chance the Rapper",
    "Chappell Roan",
    "Charley Crockett",
    "Childish Gambino",
    "Christone \"Kingfish\" Ingram",
    "Cigarettes After Sex",
    "Clairo",
    "Cold War Kids",
    "DOPE LEMON",
    "Daniel Caesar",
    "Danny Brown",
    "Daryl Hall & John Oates",
    "De La Soul",
    "Del The Funky Homosapien",
    "Dinosaur Jr.",
    "Dire Straits",
    "Dom Dolla",
    "Drug Church",
    "Drugdealer",
    "Dua Lipa",
    "Earl Sweatshirt",
    "Electric Light Orchestra",
    "Elton John",
    "Eminem",
    "Empire Of The Sun",
    "FISHER",
    "Fall Out Bay",
    "Father John Misty",
    "Flatbush Zombies",
    "Fleet Foxes",
    "Florence + The Machine",
    "Flume",
    "Foo Fighters",
    "Free Throw",
    "GZA",
    "Geese",
    "Ghostface Killah",
    "Green Day",
    "Greta Van Fleet",
    "H.E.R.",
    "Harrison Gordon",
    "Harvey Danger",
    "IDLES",
    "J Balvin",
    "J. Cole",
    "JID",
    "Jack White",
    "Jack's Mannequin",
    "Jalen Ngonda",
    "Japanese Breakfast",
    "Jay Rock",
    "John Summit",
    "Joni Mitchell",
    "Joyce Manor",
    "Jungle",
    "Kacey Musgraves",
    "Khruangbin",
    "King Princess",
    "Knuckle Puck",
    "Lana Del Rey",
    "Little Simz",
    "Mac DeMarco",
    "Maggie Rogers",
    "Major Lazer",
    "Metallica",
    "Modern Baseball",
    "Nas",
]

# Expected YES - based on user's patterns
EXPECTED_YES = [
    # Hip-hop/rap (strong matches)
    "Naughty By Nature",
    "Nicki Minaj",
    "Odd Future",
    "Offset",
    "Outkast",
    "Pharrell Williams",
    "Playboi Carti",
    "Post Malone",
    "Public Enemy",
    "Pusha T",
    "Rae Sremmurd",
    "Raekwon",
    "Rico Nasty",
    "Run The Jewels",
    "ScHoolboy Q",
    "Sheck Wes",
    "Ski Mask The Slump God",
    "Slum Village",
    "Snoop Dogg",
    "Souls Of Mischief",
    "Steve Lacy",
    "Teezo Touchdown",
    "THE SCOTTS",
    "The Pharcyde",
    "Vince Staples",
    "Westside Gunn",

    # Emo/pop punk/post-hardcore (strong matches)
    "Neck Deep",
    "New Found Glory",
    "Origami Angel",
    "Oso Oso",
    "PUP",
    "Paramore",
    "Pierce The Veil",
    "Predisposed.",
    "Prince Daddy & the Hyena",
    "Real Friends",
    "Reggie And The Full Effect",
    "Say Anything",
    "Senses Fail",
    "Sincere Engineer",
    "Something Corporate",
    "Sorority Noise",
    "Spanish Love Songs",
    "Sweet Pill",
    "Thank You, I'm Sorry",
    "The Devil Wears Prada",
    "The Red Jumpsuit Apparatus",
    "The Used",
    "Tigers Jaw",

    # Indie rock/alt (strong matches)
    "Peach Pit",
    "Phantogram",
    "Phoenix",
    "Pinegrove",
    "Pixies",
    "Portugal. The Man",
    "Rainbow Kitten Surprise",
    "Remi Wolf",
    "Rex Orange County",
    "Richy Mitch & The Coal Miners",
    "Royal Blood",
    "Royel Otis",
    "Saint Motel",
    "Sam Fender",
    "Sky Ferreira",
    "Soccer Mommy",
    "Sonic Youth",
    "St. Vincent",
    "Sudan Archives",
    "Sufjan Stevens",
    "Suki Waterhouse",
    "Tash Sultana",
    "The 1975",
    "The Beaches",
    "The Black Keys",
    "The Chats",
    "The Cranberries",
    "The Cure",
    "The Japanese House",
    "The Killers",
    "The Last Dinner Party",
    "The Linda Lindas",
    "The Lumineers",
    "The Marías",
    "The National",
    "The Neighbourhood",
    "The Nude Party",
    "The Paper Kites",
    "The Shins",
    "The Smashing Pumpkins",
    "The Smiths",
    "The Wallflowers",
    "The Walters",
    "The White Stripes",
    "The Weeknd",
    "Vampire Weekend",
    "Waxahatchee",
    "Wet Leg",
    "Wilco",
    "Wild Rivers",
    "Wunderhorse",
    "girl in red",
    "my bloody valentine",
    "saturdays at your place",

    # Electronic/dance (good matches)
    "Passion Pit",
    "RÜFÜS DU SOL",
    "Skrillex",
    "Sofi Tukker",
    "STRFKR",
    "The Avalanches",
    "The Blessed Madonna",

    # Rock legends/grunge (good matches)
    "Pearl Jam",
    "Queens of the Stone Age",
    "Radiohead",
    "Rage Against The Machine",
    "Red Hot Chili Peppers",
    "Social Distortion",
    "Stone Temple Pilots",
    "Sublime",
    "Talking Heads",
    "Temple Of The Dog",
    "The Offspring",
    "Third Eye Blind",
    "Thundercat",
    "Viagra Boys",
    "Weezer",

    # Alt/emo rap
    "nothing,nowhere.",
]

# Expected NO - artists that don't match user's patterns
EXPECTED_NO = [
    # Classic rock/oldies (user didn't keep similar artists)
    "Neil Young",
    "Paul McCartney",
    "Paul Simon",
    "Peter Frampton",
    "Peter Gabriel",
    "Pink Floyd",
    "Queen",
    "Rush",
    "Simon & Garfunkel",
    "Supertramp",
    "The Band",
    "The Beach Boys",
    "The Cars",
    "The Doobie Brothers",
    "The Kinks",
    "The Kooks",
    "The Who",
    "The Zombies",

    # Classic soul/R&B/funk (user didn't keep similar)
    "Patti Smith",
    "Roy Ayers",
    "Rufus",
    "Sade",
    "Sam & Dave",
    "Seals and Crofts",
    "Sly & The Family Stone",
    "Smokey Robinson",
    "Smokey Robinson & The Miracles",
    "Stevie Nicks",
    "Stevie Wonder",
    "The Brothers Johnson",
    "The Dramatics",
    "The Go-Go's",
    "The Isley Brothers",
    "The Maytals",
    "The O'Jays",
    "The Spinners",
    "The Temptations",

    # Pop/mainstream (user didn't keep)
    "Noah Cyrus",
    "Noah Kahan",
    "Paul Russell",
    "Robyn",
    "Saweetie",
    "Sexyy Red",
    "Shaboozey",
    "Sophie Ellis-Bextor",
    "TLC",

    # Random/miscellaneous
    "O.A.R.",
    "Pale Jay",
    "Parcels",
    "Point Point",
    "Próxima Parada",
    "Quality Control",
    "Rich Gang",
    "River Whyless",
    "Rob $tone",
    "Riton",
    "TRSH",
    "Σtella",
    "The Highwaymen",
    "The Marshall Tucker Band",
    "The Moldy Peaches",
    "The Naked And Famous",
    "The Olympians",
    "The Presidents Of The United States Of America",
    "The Purist",
    "The Sheepdogs",
    "The Thing",
    "Thee Sacred Souls",
    "Thirty Seconds To Mars",
    "Three Dog Night",
    "Tracy Chapman",
    "Tanya Tucker",
    "THE ANXIETY",
    "THE SCOTTS",
    "Waka Flocka Flame",
    "Wiz Khalifa",
    "Yung Gravy",

    # Country
    "Sturgill Simpson",

    # Ska/reggae
    "Slightly Stoopid",
    "SOB X RBE",
    "Sugar Ray",

    # Jam bands
    "Palace",
]

# Read current "actually listen to" section
with open('my_artists.txt', 'r') as f:
    lines = f.readlines()

confirmed_artists = []
in_keep_section = False
for line in lines:
    if line.strip() == "# ARTISTS YOU ACTUALLY LISTEN TO (65)":
        in_keep_section = True
        continue
    if line.strip().startswith("# ARTISTS TO REVIEW"):
        break
    if in_keep_section and line.strip() and not line.strip().startswith('#'):
        confirmed_artists.append(line.strip())

# Add above Nas selections
confirmed_artists.extend(ABOVE_NAS)
confirmed_artists = sorted(list(set(confirmed_artists)))

# Write reorganized file
with open('my_artists.txt', 'w') as f:
    f.write("# ========================================\n")
    f.write(f"# CONFIRMED KEEP ({len(confirmed_artists)} artists)\n")
    f.write("# ========================================\n")
    for artist in confirmed_artists:
        f.write(f"{artist}\n")

    f.write("\n")
    f.write("# ========================================\n")
    f.write(f"# EXPECTED YES ({len(EXPECTED_YES)} artists)\n")
    f.write("# Based on your selections, likely yes\n")
    f.write("# Delete any you DON'T want\n")
    f.write("# ========================================\n")
    for artist in sorted(EXPECTED_YES):
        f.write(f"{artist}\n")

    f.write("\n")
    f.write("# ========================================\n")
    f.write(f"# EXPECTED NO ({len(EXPECTED_NO)} artists)\n")
    f.write("# Based on your selections, likely no\n")
    f.write("# Keep any you DO want\n")
    f.write("# ========================================\n")
    for artist in sorted(EXPECTED_NO):
        f.write(f"{artist}\n")

print(f"✓ Organized my_artists.txt into categories:")
print(f"  - Confirmed Keep: {len(confirmed_artists)} artists")
print(f"  - Expected Yes: {len(EXPECTED_YES)} artists")
print(f"  - Expected No: {len(EXPECTED_NO)} artists")
print(f"\nReview the file and make any adjustments!")
