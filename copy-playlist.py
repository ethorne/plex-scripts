#!/usr/bin/env python
import os
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
from plexapi.audio import Track

def main():
    for required_env_var in ["PLEX_URL", "PLEX_TOKEN", "SOURCE"]:
        if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
            print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
            return False

    PLEX_URL = os.environ["PLEX_URL"].strip()
    PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()
    SOURCE = os.environ["SOURCE"].strip()
    DESTINATION = os.environ["DESTINATION"] if os.environ["DESTINATION"] else f"{SOURCE} COPY"

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    tunes = plex.library.section('tunes')

    print(f"SOURCE      - {SOURCE}")
    print(f"DESTINATION - {DESTINATION}")

    # iterate over all playlists
    for playlist in plex.playlists():
        playlist_title = playlist.title.strip()

        if playlist_title != SOURCE: continue

        print(f"copying playlist \"{playlist_title}\" to \"{DESTINATION}\"")
        tunes.createPlaylist(DESTINATION, playlist.items())

if __name__ == "__main__":
    if main(): exit(0)
    else: exit(1)
