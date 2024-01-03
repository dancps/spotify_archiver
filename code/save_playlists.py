# from dotenv import load_dotenv
import argparse
import json
import logging
import os

import progressbar as pb
import requests
import spotipy
from danfault.logs import Loggir

from spotify_archiver.authenticate import Authentication
from termcolor import colored

pb.streams.wrap_stderr()


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
            if (image_dict['height'] is None) or (image_dict['width'] is None):
                image_name = "cover.png"
            else:
                image_name = f"cover{image_dict['height']}x{image_dict['width']}.png"
            image_folder = os.path.join(folder, "images")
            if not os.path.isdir(image_folder):
                os.makedirs(image_folder)
            image_path = os.path.join(image_folder, image_name)

            img_data = requests.get(image_dict['url']).content
            with open(image_path, 'wb') as handler:
                handler.write(img_data)

            image_paths_list.append(image_path)
        return image_paths_list

    def download(self):
        playlists = self.sp.user_playlists(self.user)

        # list_playlist_steps = []
        playlists_list = []
        self.logger.info("Getting playlists")
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                self.logger.debug("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
                playlists_list.append(playlist)
            if playlists['next']:
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

            playlist_name = p['name']
            self.logger.info(f"{colored(playlist_name, attrs=['bold']):40}")

            # Creates a dir for each playlist
            playlist_dir = f'data/raw_data/{self.make_saveable_name(playlist_name)}'
            if not os.path.isdir(playlist_dir):
                self.logger.debug(f"Creating {playlist_dir} dir")
                os.makedirs(playlist_dir)

            # Saves metadata about it in the file
            infofile_path = os.path.join(playlist_dir, f"{self.make_saveable_name(playlist_name)}.json")
            with open(infofile_path, 'w') as fl:
                json.dump(p, fl)

            # TODO: download the playlist image
            # image_path = os.path.join(playlist_dir, f"image.png")
            self.logger.debug("Saving images")
            # for img in p['images']:
            #     print(img)
            saved_files = self.download_playlist_images(
                list_of_images=p['images'],
                folder=playlist_dir
                )
            self.logger.debug("Saved: "+", ".join(saved_files))

            # start to get the playlist's tracks
            results = self.sp.user_playlist_tracks(self.user, p['id'])

            tracks = results['items']
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            # Saves the tracks to a json
            tracks_file = os.path.join(playlist_dir, "tracks.json")
            with open(tracks_file, 'w') as fl:
                json.dump(tracks, fl)

            # Test and prints the tracks
            have_error = False
            for track_no, track in enumerate(tracks):
                try:
                    track_name = track['track']['name']
                    if self.debug and self.verbose:
                        self.logger.debug(f"  - {track_no:3d}: {track_name}")
                except TypeError as e:
                    print(colored(": error :", 'red'))
                    print(json.dumps(track))
                    error_log = os.path.join(playlist_dir, "error.log")
                    with open(error_log, 'w') as fl:
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
            self.logger.error("Error in playlists:\n  - "+"\n  - ".join(error_list))

        # bar


def main():

    parser = argparse.ArgumentParser()
    # parser.add_argument('-i', '--input', required=True, type=str, help='input')
    parser.add_argument('-o', '--output', default='.', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-d', '--debug', help='increase output verbosity', action='store_true')
    parser.add_argument('-L', '--long-output', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()

    playlists = RawPlaylists(
        verbose=args.verbose,
        debug=args.debug)
    playlists.download()


if __name__ == "__main__":
    main()