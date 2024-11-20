#!/usr/bin/env python
import datetime
from et_logger import *
import json
import os
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
from plexapi.audio import Track
import re


OLD_PATH='/media/lucien/media'

def is_good_match(logger, search_result, music_file_path, track_artist, track_album):
    logger.trace(f"looking at search_result: {search_result}", color=Colors.CYAN)
    with indent(logger):

        logger.trace_n(f"it should be a track --", color=Colors.YELLOW)
        if not isinstance(search_result, Track):
            logger.trace("FAIL", color=Colors.RED, bold=True)
            return False
        logger.trace("PASS", color=Colors.GREEN, bold=True)

        logger.trace_n(f"it should be in 'tunes' --", color=Colors.YELLOW)
        if search_result.section().title != 'tunes':
            logger.trace("FAIL", color=Colors.RED, bold=True)
            return False
        logger.trace("PASS", color=Colors.GREEN, bold=True)

        if track_artist is not None:
            logger.trace_n(f"artist should match `'{search_result.artist().title}' == '{track_artist}'` --", color=Colors.YELLOW)
            if search_result.artist().title != track_artist:
                logger.trace("FAIL", color=Colors.RED, bold=True)
                return False
            logger.trace("PASS", color=Colors.GREEN, bold=True)
        else:
            logger.trace("(skipping track_artist comparison)")

        if track_album is not None:
            logger.trace_n(f"album should match `'{search_result.album().title}' == '{track_album}'` --", color=Colors.YELLOW)
            if search_result.album().title != track_album:
                logger.trace("FAIL", color=Colors.RED, bold=True)
                return False
            logger.trace("PASS", color=Colors.GREEN, bold=True)
        else:
            logger.trace("(skipping track_album comparison)")

        logger.trace_n(f"it should not be same as the one already in the playlist " +
                f"`'{search_result.media[0].parts[0].file}' != '{music_file_path}'` --", color=Colors.YELLOW)
        if search_result.media[0].parts[0].file == music_file_path:
            logger.trace("FAIL", color=Colors.RED, bold=True)
            return False
        logger.trace("PASS", color=Colors.GREEN, bold=True)

        logger.trace_n(f"it should not contain the old file path" +
                f"`'{search_result.media[0].parts[0].file}.count('{OLD_PATH}') == 0` --", color=Colors.YELLOW)
        if search_result.media[0].parts[0].file.count(OLD_PATH) != 0:
            logger.trace("FAIL", color=Colors.RED, bold=True)
            return False
        logger.trace("PASS", color=Colors.GREEN, bold=True)

        logger.trace("adding to filtered results!")
        return True

def main():
    for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
        if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
            print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
            return False

    PLEX_URL = os.environ["PLEX_URL"].strip()
    PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()
    LOG_LEVEL = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ.keys() else LogLevel.INFO

    logger = Logger(int(LOG_LEVEL))

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    tunes = plex.library.section('tunes')

    logger = Logger(LogLevel.TRACE)

    results={
        "playlists with perfect matches": [],
        "playlists with discrepancies": []
    }
    # iterate over all playlists
    for playlist in plex.playlists():
        baddies=[]
        no_match_baddies=[]

        logger.info(f"looking at playlist \"{playlist.title.strip()}\"", bold=True)
        logger.indent_increase()

        # iterate over all tracks in playlist
        for track in playlist.items():
            filtered_results = []

            if not isinstance(track, Track): continue
            music_file_path = track.media[0].parts[0].file

            if music_file_path.count(OLD_PATH) == 0:
                logger.trace(f"looking at {track.title}", color=Colors.BLUE)
                logger.indent_increase()
                logger.trace(f"this file looks fine! it's path does not contain {OLD_PATH}")
                # TODO - add to playlist
                logger.indent_decrease()
                continue

            # some of these Track objects are busted and plex has a hard time pulling information
            # so pull the file name and artist title to use in case we need it later
            file_name = music_file_path[music_file_path.rfind('/') + 1 : music_file_path.rfind('.')]
            file_name = re.sub(r'^[0-9]+', '', file_name).strip()
            artist_title = music_file_path.split('/')[-3:][0]

            # try to find a match
            track_title_or_else = track.title if track.title else file_name + ' (track.title unavailable)'
            logger.debug(f"looking at {track_title_or_else}", color=Colors.BLUE)
            logger.indent_increase()

            try:
                track_title = track.title if track.title else file_name
                search_results = tunes.searchTracks(title=track_title, filters={"artist.title":track.artist().title})
                logger.trace(f"number of results: {len(search_results)}", color=Colors.PURPLE)
                for search_result in search_results:
                    if not is_good_match(logger,
                                         search_result,
                                         music_file_path,
                                         track.artist().title,
                                         track.album().title): continue
                    filtered_results.append(search_result)
            except Exception as e:
                logger.debug(f"~~~ trouble processing {music_file_path}")
                logger.debug( "~~~ attempting to process with file name")
                search_results = tunes.searchTracks(title=file_name.lower(), filters={"artist.title":artist_title})
                logger.trace(f"number of results: {len(search_results)}", color=Colors.PURPLE)
                for search_result in search_results:
                    if not is_good_match(logger,
                                         search_result,
                                         music_file_path,
                                         None,
                                         None): continue
                    filtered_results.append(search_result)



            num_results = len(filtered_results)
            logger.trace(f"number of matches: {num_results}", color=Colors.PURPLE, bold=num_results==1)

            if num_results == 1:
                logger.indent_decrease()
                # TODO - add to playlist
                continue


            if num_results == 0:
                no_match_baddies.append(music_file_path)
                # TODO - allow for custom search?
            else:
                # there is more than one result!
                # TODO - prompt user to select from list (or allow for custom search?)
                baddie = {
                    "file": music_file_path,
                    "matches": []
                }
                logger.indent_increase()
                for i in range(0, num_results):
                    path = filtered_results[i].media[0].parts[0].file
                    logger.debug(path, color=Colors.PURPLE)
                    baddie["matches"].append(path)
                baddies.append(baddie)
                logger.indent_decrease()
            logger.indent_decrease()

        if len(baddies) == 0 and len(no_match_baddies) == 0:
            logger.info('this playlist had all perfect matches!', color=Colors.GREEN)
            results["playlists with perfect matches"].append(playlist.title)
            logger.debug("\n---\n")
            logger.indent_decrease()
            continue

        results["playlists with discrepancies"].append({
            "playlist": playlist.title,
            "baddies_with_no_match": no_match_baddies,
            "baddies": baddies
        })

        logger.indent_decrease()
        logger.debug("\n---\n")

    json_file = f"fix-playlists.{str(datetime.datetime.now()).replace(' ', '_')}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)
    log_file = logger.dump(file_name="fix-playlists", use_date_suffix=True)

    logger.info("all done! scope the logs")
    logger.info(f"json output: {json_file}")
    logger.info(f"log output: {log_file}")
    return True

if __name__ == "__main__":
    if main(): exit(0)
    else: exit(1)
