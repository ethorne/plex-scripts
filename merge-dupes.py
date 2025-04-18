#!/usr/bin/env python

import os
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

# stolen from this reddit comment, modified a lil:
# https://www.reddit.com/r/PleX/comments/lw4d6o/comment/jj40u56/

def main():
    for var in ["PLEX_URL", "PLEX_TOKEN"]:
        if var not in os.environ.keys() or os.environ[var].strip() in [None, ""]:
            print(f"{var} not set! run `. setenv.sh` (create from template if it doesn't exist)")
            return False

    PLEX_URL = os.environ["PLEX_URL"].strip()
    PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

    # Log in and get all albums in library
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    tunes = plex.library.section('tunes')
    albums = tunes.albums()

    # Create a dictionary to store albums by name and artist
    album_dict = {}
    for album in albums:
        key = f"{album.title} - {album.parentTitle}"
        if key not in album_dict:
            album_dict[key] = []
        album_dict[key].append(album)

    # Find duplicate albums
    dupe_albums = []
    for key, album_arr in album_dict.items():
        if len(album_arr) > 1:
            dupe_albums.append(album_arr)

    # Print list of duplicate albums
    if not dupe_albums:
        print("No duplicate albums found.")
        return True

    for albums in dupe_albums:
        #for albums in dupe_albums:
        #    print(f"{album.title} - {album.parentTitle}")
        print(f"{albums[0].title} - {albums[0].parentTitle}")


    return True

if __name__ == "__main__":
    if main(): exit(0)
    else: exit(1)
