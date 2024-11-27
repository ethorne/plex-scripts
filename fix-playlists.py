#!/usr/bin/env python
import datetime
from et_logger import *
import json
import os
from plexapi.server import PlexServer # supports python 3.9 as of 2024nov18
from plexapi.audio import Track
import re

OLD_PATH='/media/lucien/media'

cache = {}

def get_file_location(track):
    return track.media[0].parts[0].file

# appends track to resutls, and caches if it's not already in the cache
def handle_found_track(logger, results, playlist, track, message=None):
    results[playlist.title.strip()]["tracks"].append(track)

    # cache it if it's not already there!
    if not get_file_location(track) in cache.keys():
        cache[get_file_location(track)] = track

    if message: logger.info(message)
    else: logger.info(f"found! {track}")

# returns True if track found in cache, false if not
# TODO - this never resulted in a cache hit - fix it!
def check_cache_and_handle_found_track(logger, results, playlist, track):
    if not get_file_location(track) in cache.keys(): return False
    handle_found_track(logger, results, playlist, track, "got a cache hit!")
    return True

def merge_results(filtered_results, filtered_results_from_search):
    ret = filtered_results
    already_have_files = []
    for result in filtered_results:
        already_have_files.append(get_file_location(result))

    for result in filtered_results_from_search:
        if get_file_location(result) in already_have_files: continue
        ret.append(result)

    return ret

# some of these Track objects are busted and plex has a hard time pulling information
# so pull the file name and artist title to use in case we need it later
# returns a tuple of (track_title, artist_title)
def get_track_and_artist_title_from_file_name(track):
    music_file_path = get_file_location(track)
    track_title = music_file_path[music_file_path.rfind('/') + 1 : music_file_path.rfind('.')]
    track_title = re.sub(r'^[0-9]+', '', track_title).strip()
    artist_title = music_file_path.split('/')[-3:][0]
    return (track_title, artist_title)

# searches for the track and filters results
# returns filtered results
def do_search(logger, library, track, broad_search=False, use_file_parts=False):
    # collect info in a nullsafe manner
    (track_title_from_file, artist_title_from_file) = get_track_and_artist_title_from_file_name(track)
    track_title = track.title if track.title else track_title_from_file
    artist_title = track.artist().title if track.artist().title else artist_title_from_file
    album_title = track.album().title if track.album().title else None

    search_title = track_title_from_file if use_file_parts else track_title
    search_artist = artist_title_from_file if use_file_parts else artist_title

    filtered_results = []
    all_results = []

    try:
        if broad_search:
            all_results = library.searchTracks(title=search_title.strip(),
                                          filters={"artist.title":search_artist.strip()})
        else:
            all_results = library.search(f"{search_title.strip()} {search_artist.strip()}")
    except Exception as e:
        # this is probably because the track title has characters that make the HTTP request fail
        # search again, but use the file name (which will likely not have those characters in it)
        logger.debug(f"~~~ trouble processing {music_file_path}")
        logger.debug( "~~~ attempting to process with file name")
        if broad_search:
            all_results = library.searchTracks(title=track_title_from_file,
                                          filters={"artist.title":artist_title_from_file})
        else:
            all_results = library.search(track_title)

    logger.trace(f"number of results: {len(all_results)}", color=Colors.PURPLE)
    for search_result in all_results:
        if not is_good_match(logger,
                             search_result,
                             get_file_location(track),
                             artist_title,
                             album_title): continue
        filtered_results.append(search_result)

    return filtered_results

# given a search result, determines if this is a good match by comparing to the other track
# the log lines are basically comments here, look at those if you're confused
# this would look a lot cleaner if I didn't want all the logging...
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
            logger.trace_n(f"artist should match `'{search_result.artist().title}' " +
                           f"== '{track_artist}'` --", color=Colors.YELLOW)
            if search_result.artist().title != track_artist:
                logger.trace("FAIL", color=Colors.RED, bold=True)
                return False
            logger.trace("PASS", color=Colors.GREEN, bold=True)
        else:
            logger.trace("(skipping track_artist comparison)")

        if track_album is not None:
            logger.trace_n(f"album should match `'{search_result.album().title}' " +
                           f"== '{track_album}'` --", color=Colors.YELLOW)
            if search_result.album().title != track_album:
                logger.trace("FAIL", color=Colors.RED, bold=True)
                return False
            logger.trace("PASS", color=Colors.GREEN, bold=True)
        else:
            logger.trace("(skipping track_album comparison)")

        logger.trace_n(f"it should not be same as the one already in the playlist " +
                       f"`'{search_result.media[0].parts[0].file}' != '{music_file_path}'` --",
                       color=Colors.YELLOW)
        if get_file_location(search_result) == music_file_path:
            logger.trace("FAIL", color=Colors.RED, bold=True)
            return False
        logger.trace("PASS", color=Colors.GREEN, bold=True)

        logger.trace_n(f"it should not contain the old file path" +
                       f"`'{search_result.media[0].parts[0].file}.count('{OLD_PATH}') == 0` --",
                       color=Colors.YELLOW)
        if get_file_location(search_result).count(OLD_PATH) != 0:
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
        logger.info(f"   file: {get_file_location(option)}", color=color)
        logger.info("")
    logger.info("")

# interactive, asks the user for input
# returns the result, which can be None
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
                if get_file_location(result).count(OLD_PATH) != 0: continue
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
            all_filtered_results = []

            if not isinstance(track, Track): continue
            music_file_path = get_file_location(track)

            logger.info(f"looking at {track.title if track.title else get_file_location(track)}",
                        color=Colors.BLUE)
            logger.indent_increase()

            # if this file is not broken (i.e. has the OLD_PATH), don't do all the searching
            if music_file_path.count(OLD_PATH) == 0:
                handle_found_track(logger, results, playlist, track,
                                   f"this file looks fine! it's path does not contain {OLD_PATH}")
                logger.indent_decrease()
                continue

            # if this file has already been found, don't do all the searching (again)
            # if check_cache_and_handle_found_track(logger, results, playlist, track): continue

            # try to find a match
            with indent(logger):
                all_filtered_results = do_search(logger, tunes, track)

            # if we got one: we're done
            num_results = len(all_filtered_results)
            if num_results == 1:
                handle_found_track(logger, results, playlist, all_filtered_results[0])
                logger.indent_decrease()
                continue

            # we didn't find one: broaden the search
            filtered_results_from_second_search = []
            logger.info(f"got {num_results} filtered results! searching the whole server now",
                        color=Colors.PURPLE, bold=num_results==1)
            with indent(logger):
                filtered_results_from_second_search = do_search(logger,
                                                                tunes,
                                                                track,
                                                                broad_search=True)

            # if we got one: we're done
            num_results = len(filtered_results_from_second_search)
            if num_results == 1:
                handle_found_track(logger, results, playlist, filtered_results_from_second_search[0])
                logger.indent_decrease()
                continue

            all_filtered_results = merge_results(all_filtered_results, filtered_results_from_second_search)

            # we didn't find one: broaden the search even more
            filtered_results_from_third_search = []
            if num_results > 1:
                logger.info(f"STILL got {num_results} filtered results! " +
                            "searching the whole server but with file parts",
                            color=Colors.PURPLE, bold=num_results==1)
                with indent(logger):
                    filtered_results_from_third_search = do_search(logger,
                                                                   tunes,
                                                                   track,
                                                                   broad_search=True,
                                                                   use_file_parts=True)

            num_results = len(filtered_results_from_third_search)

            if num_results == 1:
                handle_found_track(logger, results, playlist, filtered_results_from_third_search[0])
                logger.indent_decrease()
                continue

            all_filtered_results = merge_results(all_filtered_results, filtered_results_from_third_search)
            logger.debug(f"found {num_results} in that third search", color=Colors.PURPLE, bold=num_results==1)
            logger.debug(f"found {len(all_filtered_results)} overall", color=Colors.PURPLE, bold=num_results==1)

            # no good match found! time to get interactive
            resolution = prompt_for_resolution(logger, plex, music_file_path, all_filtered_results)
            if resolution is not None:
                handle_found_track(logger, results, playlist, resolution, "user selected resolution!")
                logger.indent_decrease()
                continue

            # well, fuck. we failed
            # put the bad track back in there (maybe to fix it manually in plex later? idk)
            # and mark this as imperfect
            handle_found_track(logger, results, playlist, track, "no match was found for this :(")
            results[playlist.title.strip()]["perfect"] = False
            results[playlist.title.strip()]["discrepancies"].append(music_file_path)

            logger.indent_decrease()

        if results[playlist.title.strip()]["perfect"]:
            logger.info('this playlist had all perfect matches!', color=Colors.GREEN)

        logger.indent_decrease()
        logger.debug("\n---\n")

    log_file = logger.dump(file_name="fix-playlists", use_date_suffix=True)


    for playlist_name in results.keys():
        result = results[playlist_name]
        old_playlist = result.pop("playlist_object")
        tracks = result.pop("tracks")

        if not result["perfect"]:
            logger.info("THIS PLAYLIST HAS BUSTED TRACKS STILL!!!",
                        bold=True, color=Colors.RED)

        for i in range(0,len(tracks)):
            track = tracks[i]
            logger.info(f"{i + 1}. {track.artist().title} - {track.title}", color=Colors.BLUE)

        new_playlist_name = playlist_name + " [FIXED]"
        logger.info(f"would you like to create this playlist? name: '{new_playlist_name}'",
                    bold=True, color=Colors.CYAN)
        choice = ""
        while choice not in ["y", "n"]:
            choice = input("y/n: ")
        if choice == "n": continue

        tunes.createPlaylist(new_playlist_name, tracks)
        logger.info(f"'{new_playlist_name}' has been created!",
                    bold=True, color=Colors.PURPLE)

        logger.info(f"would you like to delete the old playlist? " +
                    f"name: '{old_playlist.title}'", bold=True, color=Colors.RED)
        choice = ""
        while choice not in ["y", "n"]:
            choice = input("y/n: ")
        if choice == "n": continue
        old_playlist.delete()
        logger.info(f"'{old_playlist.title}' has been deleted! farewell!",
                    bold=True, color=Colors.RED)

    # do this after the above loop because that playlist_object isn't serializable!
    json_file = f"fix-playlists.{str(datetime.datetime.now()).replace(' ', '_')}.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("scope the logs")
    logger.info(f"json output: {json_file}")
    logger.info(f"log output: {log_file}")
    logger.info("\n\nthat's it!")
    logger.info("g'bye!")
    return True

if __name__ == "__main__":
    if main(): exit(0)
    else: exit(1)
