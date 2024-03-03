import argparse
import json
import os
from datetime import datetime as dt

import numpy as np
import pandas as pd

# from progress.bar import Bar
import progressbar as pb
import spotipy

# import matplotlib.pyplot as plt
from danfault.logs import Loggir
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

pb.streams.wrap_stderr()

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
    parser.add_argument("-d", "--data-folder", default="data", type=str, help="input")
    parser.add_argument(
        "-S",
        "--summary-database",
        default="data/analysis/raw_data_summary_database.csv",
        type=str,
        help="summary database",
    )
    parser.add_argument(
        "-D", "--debug", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "-o", "--overwrite", help="overwrite outputs", action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--multichoice",
        choices=["a", "b", "c"],
        nargs="+",
        type=str,
        help="multiple types of arguments. May be called all at the same time.",
    )
    args = parser.parse_args()

    logger = Loggir()

    scope = "playlist-read-private"

    sp_oauth = SpotifyOAuth(scope=scope)
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    if not os.path.isdir(args.data_folder):
        logger.error(f"The path {args.data_folder} is not a folder")
        raise ValueError(f"The path {args.data_folder} is not a folder")

    raw_data_path = os.path.join(args.data_folder, "raw_data")

    musics_path = os.path.join(args.data_folder, "musics")
    musics_raw_path = os.path.join(musics_path, "raw_data")

    if not os.path.isdir(musics_raw_path):
        logger.debug("Creating raw data of musics folder")
        os.makedirs(musics_raw_path)

    track_id_set = set()

    if (not os.path.exists(args.summary_database)) or args.overwrite:
        df = pd.DataFrame()
        for _, playlist in enumerate(
            pb.progressbar(os.listdir(raw_data_path), redirect_stdout=True)
        ):
            playlist_path = os.path.join(raw_data_path, playlist)
            metadata_path = os.path.join(playlist_path, f"{playlist}.json")
            tracks_path = os.path.join(playlist_path, f"tracks.json")

            with open(tracks_path, "r") as fl:
                tracks_data = json.load(fl)
            with open(metadata_path, "r") as fl:
                metadata = json.load(fl)

            logger.info(f"{playlist}")
            for track in tracks_data:
                temp_dict = {
                    "added_at": track["added_at"],
                    "track_id": track["track"]["id"],
                    "track_name": track["track"]["name"],
                    "track_type": track["track"]["type"],
                    "track_artists": [
                        artist["name"] for artist in track["track"]["artists"]
                    ],
                    # "added_at": track['added_at'],
                    # "added_at": track['added_at'],
                }
                temp = pd.DataFrame(temp_dict)
                if args.debug:
                    logger.debug(temp.shape)
                    logger.debug(temp.columns)
                    logger.debug(temp)

                df = pd.concat([df, pd.DataFrame(temp)])

        print(df)
        output_csv_folder = os.path.join(args.data_folder, "analysis")
        if not os.path.isdir(output_csv_folder):
            logger.debug(f"Creating {output_csv_folder}")
            os.makedirs(output_csv_folder)
        output_csv_path = os.path.join(
            output_csv_folder, "raw_data_summary_database.csv"
        )
        df.to_csv(output_csv_path)
    else: 
        df = pd.read_csv(args.summary_database)

    logger.info(f"Shape of dataframe: {df.shape}")
    unique_id = pd.unique(df['track_id'])
    logger.info(f"Unique IDs: {len(unique_id)}")
    unique_types = pd.unique(df['track_type'])
    logger.info(f"Unique Types: {len(unique_types)}")
    if len(unique_types)<=10:
        logger.info(f"\n  - "+"\n  - ".join(unique_types))


if __name__ == "__main__":
    init = dt.now()
    main()
    end = dt.now()
    print("Elapsed time: {}".format(end - init))
