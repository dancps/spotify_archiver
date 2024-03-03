'''

'''
import argparse
import csv
import datetime
import json
import os
from math import ceil
from time import sleep  # dbug only

import colorama  # this is necessary due to ANSI color incompatibility
import emoji
import numpy as np
import pandas as pd
import requests
import wget
from termcolor import colored
from tqdm import tqdm


def get_playlist_tracks(playlist_id, token, limit=100, offset=0):
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
    if(limit==None or limit>100 or limit<0):
        raise ValueError("Choose a valid value for limit parameter. (0>limit>=100)")
    if(offset==None or offset<0):
        raise ValueError("Choose a valid value for offset parameter. (offset>0)")
    url="https://api.spotify.com/v1/playlists/{}/tracks?limit={}&offset={}".format(playlist_id,limit,offset)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(token)
    }

    r = requests.get(url, headers=headers)

    return r

def get_tracks_list(playlist_id,token):
    '''
    

    Input: 
        playlist_id - id of the chosen playlist
        token - authentication token
    Output:
        tracks_list - list of tracks
    '''
    tracks_list = []
    # Calculates the size of 
    range_steps =range(calculate_request_steps(get_playlist_tracks(playlist_id,token),n=100))
    for step in range_steps:
        r = get_playlist_tracks(playlist_id,token,limit=100,offset=step*100)
        tracks_list.append(r)
    return tracks_list

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
    for step in range(calculate_request_steps(get_playists(user,token))):
        r = get_playists(user,token,limit=50,offset=step*50)
        playlists_list.append(r)
    return playlists_list

def calculate_request_steps(request,n=50,total=False):
    '''
    Calculates the number of required steps to get all of the available requests.

    Input: 
        request - Spotify request
    Output:
        steps - number of steps to cover all the playlists
    '''
    request = request.json()
    total_n = request['total']
    steps = ceil(int(total_n)/n)

    if(total): return steps, total_n
    else: return steps

def main():
    parser = argparse.ArgumentParser(description='Saves the playlists of the user into jsons and csvs.')
    parser.add_argument('-u','--user', required=True, help='set the user')
    parser.add_argument('-t','--token_file', default=".auth/tokens.txt", help='specifies the text file containing user token')
    parser.add_argument('--user_only', action='store_true', help='store only playlists owned by specified user')
    parser.add_argument('-f','--force', action='store_true', help='forces to save(this will overwrite the file if it already exists)')
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

        id_list = [(playlists['id'],playlists['name'],playlists['owner']['id']) for pl_step in plst_lst for playlists in pl_step.json()['items']]
        
        print("Getting "+colored(args.user,'blue',attrs=['bold'])+" and "+colored('others','red',attrs=['bold'])+" playlists.")
        progbar = tqdm(id_list,bar_format='{desc} {percentage:3.0f}%|{bar}{r_bar}',dynamic_ncols=True)
        for id,name,owner in progbar:
            # Removes emojis
            show_name = name
            for l in show_name:
                if l in emoji.UNICODE_EMOJI:
                    show_name = show_name.replace(l,"")
        
            if(owner==args.user): 
                progbar.set_description(colored("{}".format(show_name[:20]),'blue',attrs=['bold']))
                
                # Creates the json playlist folder
                playlist_json_path = os.path.join('json','playlists',args.user,name.replace("/","_"))
                if(not(args.force) and os.path.isdir(playlist_json_path)): continue # deletes after
                if(not(os.path.isdir(playlist_json_path))):
                    os.makedirs(playlist_json_path)

                # Getting chunks of playlist
                playlist = get_tracks_list(id,token)
                for playlist_part_indx,playlist_part in enumerate(playlist):
                    playlist_json = os.path.join(playlist_json_path,'{}_{}.json'.format(name.replace("/","_"),playlist_part_indx))
                    if(not(args.force) and os.path.isfile(playlist_json)): continue 
                    with open(playlist_json,'w') as fl:
                        fl.write(playlist_part.text)
                
                # Gets the info for each music
                music = [mus['track']['name'] for play in playlist for mus in play.json()['items']]
                album = [mus['track']['album']['name'] for play in playlist for mus in play.json()['items']]
                artist = [";".join([artist_s['name'] for artist_s in mus['track']['artists']]) for play in playlist for mus in play.json()['items']]
                duration_ms = [mus['track']['duration_ms'] for play in playlist for mus in play.json()['items']]
                added_at = [mus['added_at'] for play in playlist for mus in play.json()['items']]
                added_by = [mus['added_by']['id'] for play in playlist for mus in play.json()['items']]
                
                
                # Creates a folder to store the csv and cover image
                playlist_path = os.path.join('playlists',args.user,name.replace("/","_"))
                if(not(os.path.isdir(playlist_path))):
                    os.makedirs(playlist_path)

                # Saves the cover image
                cover_url = get_playlist_cover(id,token).json()[0]['url']
                wget.download(cover_url, out=os.path.join(playlist_path,"{}_cover.png".format(name.replace("/","_"))), bar="")
                
                # Saves the playlist in a csv
                playlist_csv_path = os.path.join(playlist_path,name.replace("/","_")+'.csv')
                with open(playlist_csv_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter=',')
                    writer.writerow(['name','album','artist','duration_ms','added_at','added_by'])
                    for mu in range(len(music)):
                        writer.writerow([music[mu],album[mu],artist[mu],duration_ms[mu],added_at[mu],added_by[mu]])


            else: 
                progbar.set_description(colored("{}".format(show_name[:20]),'red',attrs=['bold']))
                
                # Creates the json playlist folder
                if(not(args.user_only)):
                    playlist_json_path = os.path.join('json','playlists',"other",name.replace("/","_"))
                    if(not(args.force) and os.path.isdir(playlist_json_path)): continue # deletes after
                    if(not(os.path.isdir(playlist_json_path))):
                        os.makedirs(playlist_json_path)
                    # Getting chunks of playlist
                    playlist = get_tracks_list(id,token)
                    for playlist_part_indx,playlist_part in enumerate(playlist):
                        playlist_json = os.path.join(playlist_json_path,'{}_{}.json'.format(name.replace("/","_"),playlist_part_indx))
                        if(not(args.force) and os.path.isfile(playlist_json)): continue 
                        with open(playlist_json,'w') as fl:
                            fl.write(playlist_part.text)

                    # Gets the info for each music
                    music = [mus['track']['name'] for play in playlist for mus in play.json()['items']]
                    album = [mus['track']['album']['name'] for play in playlist for mus in play.json()['items']]
                    artist = [";".join([artist_s['name'] for artist_s in mus['track']['artists']]) for play in playlist for mus in play.json()['items']]
                    duration_ms = [mus['track']['duration_ms'] for play in playlist for mus in play.json()['items']]
                    added_at = [mus['added_at'] for play in playlist for mus in play.json()['items']]
                    added_by = [mus['added_by']['id'] for play in playlist for mus in play.json()['items']]
                    
                    # Creates a folder to store the csv and cover image
                    playlist_path = os.path.join('playlists',"other",name.replace("/","_"))
                    if(not(os.path.isdir(playlist_path))):
                        os.makedirs(playlist_path)

                    # Saves the cover image
                    cover_url = get_playlist_cover(id,token).json()[0]['url']
                    wget.download(cover_url, out=os.path.join(playlist_path,"{}_cover.png".format(name.replace("/","_"))), bar="")

                    # Saves the playlist in a csv
                    playlist_csv_path = os.path.join(playlist_path,name.replace("/","_")+'.csv')
                    with open(playlist_csv_path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile, delimiter=',')
                        writer.writerow(['name','album','artist','duration_ms','added_at','added_by'])
                        for mu in range(len(music)):
                            writer.writerow([music[mu],album[mu],artist[mu],duration_ms[mu],added_at[mu],added_by[mu]])
                


if(__name__=="__main__"):
    start = datetime.datetime.now()
    main()
    end = datetime.datetime.now()
    print("Elapsed time: {}".format(end-start))