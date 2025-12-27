#!/usr/bin/env python3
"""
Finalize artist list based on user selections
"""

# Artists user kept above Nas (to move to keep list)
SELECTED_TO_KEEP = [
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
    "Fall Out Boy",
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

# Based on user patterns, predict these artists below Nas
PREDICTED_TO_KEEP = [
    # Hip-hop/rap (strong pattern)
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
    "Wiz Khalifa",

    # Emo/pop punk/post-hardcore (strong pattern)
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
    "The Red Jumpsuit Apparatus",
    "The Used",
    "Tigers Jaw",

    # Indie rock/alt (strong pattern)
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
    "The Cars",
    "The Chats",
    "The Cranberries",
    "The Cure",
    "The Go-Go's",
    "The Japanese House",
    "The Killers",
    "The Kooks",
    "The Last Dinner Party",
    "The Linda Lindas",
    "The Lumineers",
    "The Marías",
    "The Naked And Famous",
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
    "Vampire Weekend",
    "Waxahatchee",
    "Wet Leg",
    "Wilco",
    "Wild Rivers",
    "Wunderhorse",
    "girl in red",
    "my bloody valentine",
    "saturdays at your place",

    # Electronic/dance (good pattern)
    "Passion Pit",
    "RÜFÜS DU SOL",
    "Skrillex",
    "Sofi Tukker",
    "STRFKR",
    "The Avalanches",
    "The Blessed Madonna",

    # Rock/grunge/punk (good pattern)
    "Pearl Jam",
    "Queens of the Stone Age",
    "Radiohead",
    "Rage Against The Machine",
    "Red Hot Chili Peppers",
    "Robyn",
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

    # Emo rap/alternative hip-hop
    "nothing,nowhere.",
]

# Read current file
with open('my_artists.txt', 'r') as f:
    lines = f.readlines()

# Get current "actually listen to" artists (before the review section)
keep_artists = []
in_keep_section = False
for line in lines:
    if line.strip() == "# ARTISTS YOU ACTUALLY LISTEN TO (65)":
        in_keep_section = True
        continue
    if line.strip().startswith("# ARTISTS TO REVIEW"):
        break
    if in_keep_section and line.strip() and not line.strip().startswith('#'):
        keep_artists.append(line.strip())

# Add selected artists
keep_artists.extend(SELECTED_TO_KEEP)

# Add predicted artists
keep_artists.extend(PREDICTED_TO_KEEP)

# Remove duplicates and sort
keep_artists = sorted(list(set(keep_artists)))

# Write final file
with open('my_artists.txt', 'w') as f:
    f.write("# ========================================\n")
    f.write(f"# FINAL ARTIST LIST ({len(keep_artists)} artists)\n")
    f.write("# ========================================\n")
    for artist in keep_artists:
        f.write(f"{artist}\n")

print(f"✓ Finalized artist list!")
print(f"  Total artists: {len(keep_artists)}")
print(f"  - Originally listened to: 65")
print(f"  - You selected above Nas: {len(SELECTED_TO_KEEP)}")
print(f"  - Predicted based on your taste: {len(PREDICTED_TO_KEEP)}")
print(f"\nReview my_artists.txt and remove any you don't want, then run the bot!")
