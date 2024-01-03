import os
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
from danfault.logs import Loggir
import argparse
import json
from datetime import datetime as dt

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

try:
    from termcolor import colored
except ImportError:
    def colored(inp,*s):
        return inp
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(inp,*s):
        return inp
from math import ceil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data-folder', default="data", type=str, help='input')
    parser.add_argument('-o', '--output', default='.', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()


    logger = Loggir()


    scope = "playlist-read-private"

    sp_oauth = SpotifyOAuth(scope=scope)
    sp = spotipy.Spotify(auth_manager=sp_oauth)


    if not os.path.isdir(args.data_folder):
        logger.error(f"The path {args.data_folder} is not a folder")
        raise ValueError(f"The path {args.data_folder} is not a folder")
    
    raw_data_path = os.path.join(args.data_folder,"raw_data")

    musics_path =  os.path.join(args.data_folder,"musics")
    musics_raw_path = os.path.join(musics_path,"raw_data")
    
    if not os.path.isdir(musics_raw_path):
        logger.debug("Creating raw data of musics folder")
        os.makedirs(musics_raw_path)

    track_id_set = set()
    for playlist in os.listdir(raw_data_path):
        # print(playlist)
        playlist_path = os.path.join(raw_data_path,playlist)
        metadata_path = os.path.join(playlist_path,f"{playlist}.json")
        tracks_path = os.path.join(playlist_path,f"tracks.json")
        # logger.debug(f"Tracks path: {tracks_path}")

        with open(tracks_path,'r') as fl:
            tracks_data = json.load(fl)
        with open(metadata_path,'r') as fl:
            metadata = json.load(fl)
        
        
        for track in tracks_data:

            track_id=track['track']['id']
            track_name = track['track']['name']
            analysis_file_name = os.path.join(musics_raw_path,f"{track_id}_analysis.json")
            if not os.path.isfile(analysis_file_name):
                logger.debug(f"Getting analysis for {track_id} {track_name}")
            
                response = sp.audio_analysis(track_id)
                # Saves metadata about it in the file
                with open(analysis_file_name,'w') as fl:
                    json.dump(response,fl)
            if os.path.isfile(analysis_file_name):
                # logger.debug("Loading track_id")
                track_id_set.update({track_id})

    logger.info(f"No. of tracks: {len(track_id_set)}")
    n_tracks = len(track_id_set)
    chunk_size = 30
    tracks_chunks = ceil(n_tracks/chunk_size)
    tracks_remaining = ceil(n_tracks%100)

    logger.info(f"tracks_chunks: {tracks_chunks}")
    logger.info(f"tracks_remaining: {tracks_remaining}")
    for i in range(tracks_chunks):
        nmin = (i*chunk_size)
        nmax= min(((i+1)*chunk_size)-1,n_tracks-1)
        logger.debug(f"chunk_init: {nmin} - {nmax}")
        slice_of_ids = list(track_id_set)[nmin:nmax+1]
        logger.debug(f"Getting analysis for {track_id} {track_name}")
        response = sp.audio_features(slice_of_ids)
        logger.debug(len(slice_of_ids))
        logger.debug(f"Response size: {len(response)}")

        for track in response:
            track_id = track['id']
            feature_file_name = os.path.join(musics_raw_path,f"{track_id}_features.json")
            if not os.path.isfile(feature_file_name):
                logger.debug(f"Getting features for {track_id} ")
                with open(feature_file_name,'w') as fl:
                    json.dump(track,fl)

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


        



if(__name__=='__main__'):
    init=dt.now()
    main()
    end=dt.now()
    print('Elapsed time: {}'.format(end-init))