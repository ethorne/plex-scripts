#!/usr/bin/env python
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
import os

for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
    if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
        print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")

PLEX_URL = "http://"+os.environ["PLEX_URL"].strip()+":32400"
PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

plex = PlexServer(PLEX_URL, PLEX_TOKEN)
tunes_library = plex.library.section('tunes')

# Check if the "unorganized" collection exists
collection_name = "unorganized"
existing_collections = tunes_library.collections()

# If collection "unorganized" does not exist, create it
unorganized_collection = None
for collection in existing_collections:
    if collection.title == collection_name:
        unorganized_collection = collection
        break

if unorganized_collection is None:
    unorganized_collection = tunes_library.createCollection(collection_name)

# Iterate through every album in the "tunes" library and add it to the collection
for artist in tunes_library.all():
    print(f"Adding albums: {artist.albums()} to 'unorganized' collection.")
    unorganized_collection.addItems(artist.albums())

print("All albums have been added to the 'unorganized' collection.")

