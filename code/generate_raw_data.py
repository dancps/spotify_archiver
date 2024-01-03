"""
This file will have the name changed to generate_raw_data.

By now implements the ExtraDatabase class, which will be responsible for
gathering the audio analysis and features for each track.

"""

import argparse
import json
import logging
import os
from datetime import datetime as dt

import progressbar as pb
import requests
import spotipy
from danfault.logs import Loggir
from spotipy.exceptions import SpotifyException

from spotify_archiver.authenticate import Authentication

try:
    from termcolor import colored
except ImportError:

    def colored(inp, *s):
        return inp


try:
    from tqdm import tqdm
except ImportError:

    def tqdm(inp, *s):
        return inp


from math import ceil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["all", "playlists", "analysis", "features"], type=str, help="input"
    )
    parser.add_argument("-d", "--data-folder", default="data", type=str, help="input")
    parser.add_argument("-o", "--output", default=".", type=str, help="output")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-D", "--debug", help="increase output verbosity", action="store_true")
    parser.add_argument(
        "--multichoice",
        choices=["a", "b", "c"],
        nargs="+",
        type=str,
        help="multiple types of arguments. May be called all at the same time.",
    )
    args = parser.parse_args()

    playlists = RawPlaylists(verbose=args.verbose, debug=args.debug)

    extradb = ExtraDatabase(data_folder=args.data_folder, verbose=args.verbose, debug=args.debug)

    if args.command == "all":
        extradb.get_audio_analysis()
        extradb.get_audio_features()
    elif args.command == "playlists":
        playlists.download()
    elif args.command == "analysis":
        extradb.get_audio_analysis()
    elif args.command == "features":
        extradb.get_audio_features()
    else:
        raise NotImplementedError(
            f"{args.command} doesn't exist. Choose one of the folloing: all, analysis, features"
        )


class RawPlaylists:
    def __init__(self, user=None, verbose=True, debug=False) -> None:
        scope = "playlist-read-private"

        self.logger = Loggir()
        # pb.streams.wrap_stderr()
        self.logger.info("Authenticating")
        self.auth = Authentication(scope=scope)
        self.sp = spotipy.Spotify(auth_manager=self.auth.get_auth())

        if user is None:
            self.user = os.environ.get("SPOTIFY_USER")
        else:
            self.user = user

        self.logger.info(f"User: {self.user}")

        self.verbose = verbose
        self.debug = debug

        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def get_biggest_name(self, list):
        maxlen = 0
        for i in list:
            currlen = len(i)
            if currlen > maxlen:
                maxlen = currlen
        return maxlen

    def make_saveable_name(self, name):
        return name.replace("/", "_")

    def download_playlist_images(self, list_of_images, folder):
        image_paths_list = []
        for image_dict in list_of_images:
            if (image_dict["height"] is None) or (image_dict["width"] is None):
                image_name = "cover.png"
            else:
                image_name = f"cover{image_dict['height']}x{image_dict['width']}.png"
            image_folder = os.path.join(folder, "images")
            if not os.path.isdir(image_folder):
                os.makedirs(image_folder)
            image_path = os.path.join(image_folder, image_name)

            img_data = requests.get(image_dict["url"]).content
            with open(image_path, "wb") as handler:
                handler.write(img_data)

            image_paths_list.append(image_path)
        return image_paths_list

    def download(self):
        playlists = self.sp.user_playlists(self.user)

        # list_playlist_steps = []
        playlists_list = []
        self.logger.info("Getting playlists")
        while playlists:
            for i, playlist in enumerate(playlists["items"]):
                self.logger.debug(
                    "%4d %s %s" % (i + 1 + playlists["offset"], playlist["uri"], playlist["name"])
                )
                playlists_list.append(playlist)
            if playlists["next"]:
                # list_playlist_steps.append(playlists)
                playlists = self.sp.next(playlists)
            else:
                playlists = None
        # self.logger.debug(f"Playlist offset: {p['offset']})")
        # biggest_name = get_biggest_name([x['name'] for x in p['items']])
        # print(biggest_name)
        self.logger.info("Saving tracks for the playlists")
        for i, p in enumerate(pb.progressbar(playlists_list, redirect_stdout=True)):
            # print(playlists_step)
            # for playlists_indes,playlists in playlists_step.items():
            #     print(playlists)
            # self.logger.debug("Playlist keys:\n  - "+"\n  - ".join(p.keys()))

            error_list = []

            # for i, p in enumerate(playlists['items']):
            # Debug
            # print(p.keys())
            # print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))

            playlist_name = p["name"]
            self.logger.info(f"{colored(playlist_name, attrs=['bold']):40}")

            # Creates a dir for each playlist
            playlist_dir = f"data/raw_data/{self.make_saveable_name(playlist_name)}"
            if not os.path.isdir(playlist_dir):
                self.logger.debug(f"Creating {playlist_dir} dir")
                os.makedirs(playlist_dir)

            # Saves metadata about it in the file
            infofile_path = os.path.join(
                playlist_dir, f"{self.make_saveable_name(playlist_name)}.json"
            )
            with open(infofile_path, "w") as fl:
                json.dump(p, fl)

            # TODO: download the playlist image
            # image_path = os.path.join(playlist_dir, f"image.png")
            self.logger.debug("Saving images")
            # for img in p['images']:
            #     print(img)
            saved_files = self.download_playlist_images(
                list_of_images=p["images"], folder=playlist_dir
            )
            self.logger.debug("Saved: " + ", ".join(saved_files))

            # start to get the playlist's tracks
            results = self.sp.user_playlist_tracks(self.user, p["id"])

            tracks = results["items"]
            while results["next"]:
                results = self.sp.next(results)
                tracks.extend(results["items"])

            # Saves the tracks to a json
            tracks_file = os.path.join(playlist_dir, "tracks.json")
            with open(tracks_file, "w") as fl:
                json.dump(tracks, fl)

            # Test and prints the tracks
            have_error = False
            for track_no, track in enumerate(tracks):
                try:
                    track_name = track["track"]["name"]
                    if self.debug and self.verbose:
                        self.logger.debug(f"  - {track_no:3d}: {track_name}")
                except TypeError as e:
                    print(colored(": error :", "red"))
                    print(json.dumps(track))
                    error_log = os.path.join(playlist_dir, "error.log")
                    with open(error_log, "w") as fl:
                        fl.write("ERROR PROCESSING {track_name}")
                    have_error = True
            if have_error:
                # print(colored("X",'red'))
                self.logger.error("Error in the playlist")
                error_list.append(playlist_name)
            # break
        if len(error_list) == 0:
            self.logger.info("Succesfully saved")
        else:
            self.logger.error("Error in playlists:\n  - " + "\n  - ".join(error_list))

        # bar


class ExtraDatabase:
    def __init__(self, data_folder, verbose, debug) -> None:
        scope = "playlist-read-private"

        self.logger = Loggir()
        # pb.streams.wrap_stderr()
        self.logger.info("Authenticating")
        self.auth = Authentication(scope=scope)
        self.sp = spotipy.Spotify(auth_manager=self.auth.get_auth())

        self.data_folder = data_folder
        self.verbose = verbose
        self.debug = debug

        self.raw_data_path = os.path.join(self.data_folder, "raw_data")
        self.musics_path = os.path.join(self.data_folder, "musics")
        self.musics_raw_path = os.path.join(self.musics_path, "raw_data")

    def get_audio_analysis(self, data_folder=None):
        if data_folder is None:
            data_folder = self.data_folder

        if not os.path.isdir(data_folder):
            self.logger.error(f"The path {data_folder} is not a folder")
            raise ValueError(f"The path {data_folder} is not a folder")

        if not os.path.isdir(self.musics_raw_path):
            self.logger.debug("Creating raw data of musics folder")
            os.makedirs(self.musics_raw_path)

        track_id_set = set()

        for _, playlist in enumerate(
            pb.progressbar(os.listdir(self.raw_data_path), redirect_stdout=True)
        ):
            playlist_path = os.path.join(self.raw_data_path, playlist)
            metadata_path = os.path.join(playlist_path, f"{playlist}.json")
            tracks_path = os.path.join(playlist_path, f"tracks.json")
            if self.debug:
                self.logger.debug(f"Tracks path: {tracks_path}")

            with open(tracks_path, "r") as fl:
                tracks_data = json.load(fl)
            with open(metadata_path, "r") as fl:
                metadata = json.load(fl)

            for _, track in enumerate(pb.progressbar(tracks_data, redirect_stdout=True)):
                track_id = track["track"]["id"]
                track_name = track["track"]["name"]
                track_type = track["track"]["type"]
                if track_type == "episode":
                    self.logger.debug(
                        colored("Skipping", "yellow")
                        + f" analysis for {track_id} {track_name}. (Episode)"
                    )

                    continue
                analysis_file_name = os.path.join(self.musics_raw_path, f"{track_id}_analysis.json")
                if not os.path.isfile(analysis_file_name):
                    self.logger.debug(f"Getting analysis for {track_id} {track_name}")
                    try:
                        response = self.sp.audio_analysis(track_id)
                    except SpotifyException as e:
                        self.logger.error(e)
                    else:
                        # Saves metadata about it in the file
                        with open(analysis_file_name, "w") as fl:
                            json.dump(response, fl)
                    if os.path.isfile(analysis_file_name):
                        # logger.debug("Loading track_id")
                        track_id_set.update({track_id})

        return track_id_set

    def get_ids_from_files(self, data_folder=None):
        if data_folder is None:
            data_folder = self.data_folder
        available_ids = set()
        for file in os.listdir(self.musics_raw_path):
            if file.endswith("_analysis.json"):
                id = file.replace("_analysis.json", "")
                self.logger.debug(f"Reading {file} (ID: {id})")
                available_ids.update({id})
        return available_ids

    def get_audio_features(self, data_folder=None, verbose=True, debug=False):
        if data_folder is None:
            data_folder = self.data_folder

        track_id_set = self.get_ids_from_files(data_folder)
        self.logger.info(f"No. of tracks: {len(track_id_set)}")
        n_tracks = len(track_id_set)
        chunk_size = 100
        tracks_chunks = ceil(n_tracks / chunk_size)
        tracks_remaining = ceil(n_tracks % 100)

        self.logger.info(f"tracks_chunks: {tracks_chunks}")
        self.logger.info(f"tracks_remaining: {tracks_remaining}")
        for i in range(tracks_chunks):
            nmin = i * chunk_size
            nmax = min(((i + 1) * chunk_size) - 1, n_tracks - 1)
            self.logger.debug(f"chunk_init: {nmin} - {nmax}")
            slice_of_ids = list(track_id_set)[nmin : nmax + 1]
            self.logger.debug(f"Getting analysis for {nmin}:{nmax+1}")
            try:
                response = self.sp.audio_features(slice_of_ids)
            except SpotifyException as e:
                self.logger.error(e)
                raise e
            self.logger.debug(len(slice_of_ids))
            self.logger.debug(f"Response size: {len(response)}")

            for track in response:
                track_id = track["id"]
                feature_file_name = os.path.join(musics_raw_path, f"{track_id}_features.json")
                if not os.path.isfile(feature_file_name):
                    self.logger.debug(f"Getting features for {track_id} ")
                    with open(feature_file_name, "w") as fl:
                        json.dump(track, fl)

            # logger.debug(" \n"+str(response))
            # print(response[0].keys())
            # if not os.path.isfile(analysis_file_name):
            #         logger.debug(f"Getting analysis for {track_id} {track_name}")
            #         response = sp.audio_analysis(track_id)
            #         # Saves metadata about it in the file
            #         with open(analysis_file_name,'w') as fl:
            #             json.dump(response,fl)

        # for track_id in track_id_set:
        #


if __name__ == "__main__":
    init = dt.now()
    main()
    end = dt.now()
    print("Elapsed time: {}".format(end - init))
