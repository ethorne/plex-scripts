#!/usr/bin/env python
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
import os

for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
    if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
        print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")

PLEX_URL = "http://"+os.environ["PLEX_URL"].strip()+":32400"
PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()

plex = PlexServer(PLEX_URL, PLEX_TOKEN)
