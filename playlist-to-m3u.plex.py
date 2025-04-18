#!/usr/bin/env python
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
import os

for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
    if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
        print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
        exit(1)

PLEX_URL = os.environ["PLEX_URL"].strip()
PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

exlude_these_playlists = []
include_these_playlists = ["boogie baddies for my water daddy"]

EXISTING_PREFIX='/media/lucien/media'
REPLACE_PREFIX='/Volumes/orpheus'

M3U_DIR='M3Us'

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

if not os.path.exists(M3U_DIR): os.mkdir(M3U_DIR)

for playlist in plex.playlists():
    try:
        #if playlist.title.strip() in exlude_these_playlists: continue
        if playlist.title.strip() not in include_these_playlists: continue

        print(f"syncing playlist \"{playlist.title.strip()}\"")

        m3u_path = f"{M3U_DIR}/{playlist.title}.m3u"
        paths = []

        # iterate over all playlists
        for playlist_item in playlist.items():
            # iterate over all items in playlist
            for playlist_item_parts in playlist_item.iterParts():
                music_file_path = playlist_item_parts.file
                if music_file_path is None: continue
                #music_file_path = music_file_path.replace(EXISTING_PREFIX, REPLACE_PREFIX)
                paths.append(music_file_path + "\n")

    except Exception as e:
        print('\n\n!!!!!!!!!!!ENCOUNTERED!AN!ERROR!!!!!!!!!!!')
        print(e)
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')
        continue

    # write m3u file for playlist
    with open(m3u_path, 'w', encoding='utf-8') as m3u_file:
        print(paths)
        m3u_file.writelines(paths)

    print('\n\n-----------------------------------------------------------------\n\n')
