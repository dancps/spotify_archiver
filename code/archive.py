'''

'''
import requests
import json
from math import ceil
from termcolor import colored
import colorama # this is necessary due to ANSI color incompatibility
import pandas as pd
import os
import numpy as np
from tqdm import tqdm
import datetime
import wget
import argparse


def get_playlist_tracks(playlist_id,token,limit=None,offset=None):
    '''
    Gets a Spotify request for the tracks of the playlists.

    Input: 
        playlist_id - id of the chosen playlist
        token - authentication token
        limit -  number of playlists in the request
        offset -  offset of the request
    Output:
        r - Spotify request
    '''
    if(limit==None or limit>50 or limit<0):
        raise ValueError("Choose a valid value for limit parameter. (0>limit>=50)")
    if(offset==None or offset<0):
        raise ValueError("Choose a valid value for offset parameter. (0>limit>=50)")
    url="https://api.spotify.com/v1/playlists/{}/tracks?limit={}&offset={}".format(playlist_id,limit,offset)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }

    r = requests.get(url, headers=headers)

    return r

def get_playlist_cover(playlist_id,token): # Ref: https://developer.spotify.com/console/get-playlist-images/
    '''
    Gets the cover image link of the playlist.

    Input: 
        playlist_id - id of the chosen playlist
        token - authentication token
    Output:
        r -  Spotify request
    '''
    url="https://api.spotify.com/v1/playlists/{}/images".format(playlist_id)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }

    r = requests.get(url, headers=headers)
    return r

def get_playists(user,token,limit=50,offset=0):
    '''
    Gets a Spotify request for the playlists.

    Input: 
        user - string containing the user
        token - authentication token
        limit -  number of playlists in the request
        offset -  offset of the request
    Output:
        r - Spotify request
    '''
    if(limit==None or limit>50 or limit<0):
        raise ValueError("Choose a valid value for limit parameter. (0>limit>=50)")
    if(offset==None or offset<0):
        raise ValueError("Choose a valid value for offset parameter. (0>limit>=50)")

    playlists_url = "https://api.spotify.com/v1/users/{}/playlists?limit={}&offset={}".format(user,limit,offset)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }

    r = requests.get(playlists_url, headers=headers)
    
    return r

def get_playists_list(user,token):
    '''
    Uses calculate_requset_step to get a list of available playlists. I.e., if there are 180 playlists, this will return a 4 items list with a maximum of 50 playlists in each of them.

    Input: 
        user - string containing the user
        token - authentication token
    Output:
        playlists_list - list of playlists
    '''
    playlists_list = []
    # Calculates the size of 
    for step in tqdm(range(calculate_request_steps(get_playists(user,token)))):
        r = get_playists(user,token,limit=50,offset=step*50)
        playlists_list.append(r)
    return playlists_list

def calculate_request_steps(request):
    '''
    Calculates the number of required steps to get all of the available requests.

    Input: 
        request - Spotify request
    Output:
        steps - number of steps to cover all the playlists
    '''
    request = request.json()
    
    steps = ceil(int(request['total'])/50)

    return steps

def main():
    parser = argparse.ArgumentParser(description='Saves the playlists of the user into jsons and csvs.')
    parser.add_argument('-u','--user', required=True, help='set the user')
    parser.add_argument('-t','--token_file', default=".auth/tokens.txt", help='specifies the text file containing user token')
    args = parser.parse_args()

    token_path = os.path.join(args.token_file)

    with open(token_path,'r') as tok:
        token = tok.readline().replace("\n","")
        user = args.user

        print("Getting playlists steps...")
        playlists_steps = calculate_request_steps(get_playists(user,token))

        print("Loading JSON playlists...")
        plst_lst = get_playists_list(user,token)

        json_path = os.path.join('json')

        if(not(os.path.isdir(json_path))):
            os.makedirs(json_path)

        for step,plst_step in enumerate(plst_lst):
            with open(os.path.join('json','playlists_part_{}.json'.format(step)),'w') as fl:
                fl.write(plst_step.text)

if(__name__=="__main__"):
    start = datetime.datetime.now()
    main()
    end = datetime.datetime.now()
    print("Elapsed time: {}".format(end-start))