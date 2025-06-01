#!/usr/bin/env python
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
import os

for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
    if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
        print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
        exit(1)

PLEX_URL = os.environ["PLEX_URL"].strip()
PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

include_these_playlists = ["boogie baddies for my water daddy"]


plex = PlexServer(PLEX_URL, PLEX_TOKEN)

# iterate over all playlists
for playlist in plex.playlists():
    if playlist.title.strip() not in include_these_playlists: continue

    print("[ song :: artist :: album ]")
    for track in playlist.items():
        try:
            song = track.title
            artist = track.artist().title
            album = track.album().title
            print(f"{song} :: {artist} :: {album}")
        except Exception as e:
            print('\n\n!!!!!!!!!!!ENCOUNTERED!AN!ERROR!!!!!!!!!!!')
            print(e)
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
            continue

    print('\n\n-----------------------------------------------------------------\n\n')

