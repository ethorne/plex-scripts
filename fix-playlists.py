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

def display_options(logger, options):
    color=Colors.BLUE
    for i in range(0, len(options)):
        option = options[i]
        logger.info(f"{i+1}. {option.title} - {option.album().title} - {option.artist().title}", color=color)
        logger.info(f"   file: {option.media[0].parts[0].file}", color=color)
        logger.info("")
    logger.info("")

def prompt_for_resolution(logger, plex, music_file_path, initial_options):
    color=Colors.BLUE
    with indent(logger):
        logger.info("")
        logger.info("looking for match for", color=color)
        logger.info(music_file_path, color=color)
        logger.info("")
        logger.info("options are displayed as: title - album - artist", color=color)
        logger.info("enter 's' to search", color=color)
        logger.info("enter 'x' to exit\n", color=color)
        choice = ""

        options = initial_options
        while True:
            display_options(logger, options)
            choice = input("what do you choose? ")
            while choice not in [str(i+1) for i in range(0,len(options))] + ["x", "s"]:
                choice = input("choose again dummy: ")
            if choice not in ["s", "x"]: return options[int(choice) - 1]
            if choice == "x": return None
            query=input("input a search query: ")
            search_results = plex.search(query)
            options = []
            for result in search_results:
                if not isinstance(result, Track): continue
                if result.media[0].parts[0].file.count(OLD_PATH) != 0: continue
                options.append(result)




def main():
    for required_env_var in ["PLEX_URL", "PLEX_TOKEN"]:
        if required_env_var not in os.environ.keys() or os.environ[required_env_var].strip() in [None, ""]:
            print(f"{required_env_var} not set! run `source setenv.sh` (create from template if it doesn't exist)")
            return False

    PLEX_URL = os.environ["PLEX_URL"].strip()
    PLEX_TOKEN = os.environ["PLEX_TOKEN"].strip()
    LOG_LEVEL = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ.keys() else LogLevel.INFO

    logger = Logger(level=int(LOG_LEVEL))

    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    tunes = plex.library.section('tunes')

    results={}
    # iterate over all playlists
    for playlist in plex.playlists():
        results[playlist.title.strip()] = {
            "playlist_object":playlist,
            "tracks": [],
            "perfect": True,
            "discrepancies": []
        }

        logger.info(f"looking at playlist \"{playlist.title.strip()}\"", bold=True)
        logger.indent_increase()

        # iterate over all tracks in playlist
        for track in playlist.items():
            filtered_results = []

            if not isinstance(track, Track): continue
            music_file_path = track.media[0].parts[0].file

            if music_file_path.count(OLD_PATH) == 0:
                logger.info(f"looking at {track.title}", color=Colors.BLUE)
                logger.indent_increase()
                logger.trace(f"this file looks fine! it's path does not contain {OLD_PATH}")
                logger.indent_decrease()
                results[playlist.title.strip()]["tracks"].append(track)
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

            ## TODO ##
            # these next two blocks of searching need work
            # it's prolly because the track.title is empty?
            # also, what if i get one filtered_result, eh? i dont think i append it to the playlist tracks
            # also, how confident can i really be if I just get one? prolly pass it to the prompt either way
            # on top of that - can this be wrapped up in a better function?
            # oh, and you have a indent_increase somwhere that's not being decreased later.....
            num_results = len(filtered_results)
            if num_results != 1:
                filtered_results = []
                logger.info(f"got {num_results} filtered results! searching through the whole server now")
                logger.indent_increase()
                query = track.title if track.title else file_name
                try:
                    search_results = plex.search(query)
                    logger.trace(f"number of results: {len(search_results)}", color=Colors.PURPLE)
                except Exception as e:
                    logger.info("op! got an exception searching the server", color=Colors.PURPLE)
                    logger.info("setting search_results=[]", color=Colors.PURPLE)
                    search_results=[]
                for search_result in search_results:
                    if not is_good_match(logger,
                                         search_result,
                                         music_file_path,
                                         track.artist().title,
                                         track.album().title): continue
                    filtered_results.append(search_result)
                logger.indent_decrease()

            num_results = len(filtered_results)
            if num_results != 1:
                filtered_results = []
                logger.info(f"STILL got {num_results} filtered results! searching the whole server but with file parts")
                logger.indent_increase()
                # there might be parenthetical with a remix title or something, get rid of that
                query = f"{file_name.split('(')[0].strip()} {artist_title}"
                try:
                    search_results = plex.search(query)
                    logger.trace(f"number of results: {len(search_results)}", color=Colors.PURPLE)
                except Exception as e:
                    logger.info("op! got an exception searching the server", color=Colors.PURPLE)
                    logger.info("setting search_results=[]", color=Colors.PURPLE)
                    search_results=[]
                for search_result in search_results:
                    if not is_good_match(logger,
                                         search_result,
                                         music_file_path,
                                         track.artist().title,
                                         track.album().title): continue
                    filtered_results.append(search_result)
                logger.indent_decrease()

            num_results = len(filtered_results)
            logger.trace(f"number of matches: {num_results}", color=Colors.PURPLE, bold=num_results==1)

            if num_results == 1:
                results[playlist.title.strip()]["tracks"].append(track)
                logger.indent_decrease()
                continue

            # no good match found! time to get interactive
            resolution = prompt_for_resolution(logger, plex, music_file_path, filtered_results)
            if resolution is not None:
                results[playlist.title.strip()]["tracks"].append(resolution)
                logger.info(f"selected {resolution}!")
                logger.indent_decrease()
                continue;

            # best effort - put the bad track back in there (maybe to fix it manually in plex later? idk)
            results[playlist.title.strip()]["tracks"].append(track)
            results[playlist.title.strip()]["perfect"] = False
            results[playlist.title.strip()]["discrepancies"].append(music_file_path)

        if results[playlist.title.strip()]["perfect"]:
            logger.info('this playlist had all perfect matches!', color=Colors.GREEN)
            logger.debug("\n---\n")
            logger.indent_decrease()
            continue


        logger.indent_decrease()
        logger.debug("\n---\n")

    log_file = logger.dump(file_name="fix-playlists", use_date_suffix=True)

    logger.info("all done! scope the logs")
    logger.info(f"json output: {json_file}")
    logger.info(f"log output: {log_file}")

    for playlist_name in results.keys():
        result = results["playlist_name"]
        old_playlist = results.pop("playlist_object")
        tracks = result["tracks"]
        print(json.dumps(result, indent=2))

        if not result["perfect"]:
            logger.info("THIS PLAYLIST HAS BUSTED TRACKS STILL!!!", bold=True, color=Colors.RED)

        new_playlist_name = playlist_name + " [FIXED]"
        logger.info(f"would you like to create this playlist? name: '{new_playlist_name}'", bold=True, color=Colors.CYAN)
        choice = ""
        while choice not in ["y", "n"]:
            choice = input("y/n: ")
        if choice == "n": continue

        plex.createPlaylist(new_playlist_name, tracks)
        logger.info(f"'{new_playlist_name}' has been created!", bold=True, color=Colors.PURPLE)

        logger.info(f"would you like to delete the old playlist? " +
                     "name: '{old_playlist.title}'", bold=True, color=Colors.RED)
        choice = ""
        while choice not in ["y", "n"]:
            choice = input("y/n: ")
        if choice == "n": continue
        old_playlist.delete()
        logger.info(f"'{old_playlist.title}' has been deleted! farewell!", bold=True, color=Colors.RED)

    # do this after the above loop because that playlist_object isn't serializable!
    json_file = f"fix-playlists.{str(datetime.datetime.now()).replace(' ', '_')}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("that's it!")
    logger.info("g'bye!")
    return True

if __name__ == "__main__":
    if main(): exit(0)
    else: exit(1)
