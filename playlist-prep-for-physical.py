#!/usr/bin/env python
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
import os
import shutil

# this script is for prepping a playlist to burn to a CD or record to tape

for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
    if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
        print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
        exit(1)

PLEX_URL = os.environ["PLEX_URL"].strip()
PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

include_these_playlists = ["boogie baddies for my water daddy"]

plex = PlexServer(PLEX_URL, PLEX_TOKEN)


for playlist in plex.playlists():
    try:
        playlist_title = playlist.title.strip()
        if playlist_title not in include_these_playlists: continue

        os.mkdir(playlist_title)
        print(f"copying playlist \"{playlist_title}\"")

        i = 1
        # iterate over all items in playlist
        for track in playlist.items():
            music_file_path = track.media[0].parts[0].file
            file_type = music_file_path[music_file_path.rfind('.')+1:]
            track_title = track.title
            artist_title = track.artist().title

            destination = f"{playlist_title}/{str(i).zfill(2)} - {track_title} - {artist_title}.{file_type}"
            print(f"copying '{destination}'")
            shutil.copyfile(music_file_path, destination)

            i = i + 1

    except Exception as e:
        print('\n\n!!!!!!!!!!!ENCOUNTERED!AN!ERROR!!!!!!!!!!!')
        print(e)
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
        continue

    print('\n\n-----------------------------------------------------------------\n\n')
