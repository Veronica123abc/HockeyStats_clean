#import mysql.connector
#import mysql
#import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher
import api
from sportlogiq import extract_game_info_from_schedules, get_game_numbers_from_schedules
#import sportlogiq
import scraping

import db_tools
import uuid
#import logging
import json
import requests
import browser_cookie3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
SPORTLOGIQ_USERNAME = os.getenv('SPORTLOGIQ_USERNAME')
SPORTLOGIQ_PWD = os.getenv('SPORTLOGIQ_PWD')
API_URL = os.getenv('SPORTLOGIQ_API_URL')


class apiv2:
    def __init__(self):
        self.SPORTLOGIQ_USERNAME = os.getenv('SPORTLOGIQ_USERNAME')
        self.SPORTLOGIQ_PWD = os.getenv('SPORTLOGIQ_PWD')
        self.apiurl = 'https://api.sportlogiq.com'
        login_payload = {'username': SPORTLOGIQ_USERNAME, 'password': SPORTLOGIQ_PWD}
        # use requests.Session() to handle cookies for you
        self.req = requests.Session()
        res = self.req.post(self.apiurl + '/v1/hockey/login', json=login_payload)



    def get_game_info(self, game_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/games/{game_id}')
        return response

    def get_roster(self, game_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/games/{game_id}/roster')
        return response

    def get_events(self, game_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/games/{game_id}/events/full')
        return response

    def get_compiled_events(self, game_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/games/{game_id}/events/compiled')
        return response

    def get_shifts(self, game_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/games/{game_id}/events/shifts')
        return response

    def get_leagues(self):
        response = self.req.get(self.apiurl + f'/v1/hockey/competitions')
        return response

    def get_competitions(self, league_id):
        response = self.req.get(self.apiurl + f'/v1/hockey/competitions/{league_id}')


def login():
    SPORTLOGIQ_USERNAME = os.getenv('SPORTLOGIQ_USERNAME')
    SPORTLOGIQ_PWD = os.getenv('SPORTLOGIQ_PWD')
    #username = 'veronica.eriksson580@gmail.com' #your email address
    #password = 'B1llyfjant.1'
    apiurl = 'https://api.sportlogiq.com'

    login_payload = {'username': SPORTLOGIQ_USERNAME, 'password': SPORTLOGIQ_PWD}

    # use requests.Session() to handle cookies for you
    req = requests.Session()
    res = req.post(apiurl + '/v1/hockey/login', json=login_payload)
    return req

def create_frame_to_time(game_id, source_dir):
    full_events = json.load(open(os.path.join(source_dir,f"{game_id}.json")))
    # shifts = json.load(open(os.path.join(source_dir,f"../shifts/{game_id}.json")))
    periods = [e['period'] for e in full_events['events']]
    num_periods = max(periods)
    full_map={}
    for period in range(1,num_periods+1):
        events = [(e['frame'], e['period_time']) for e in full_events['events'] if e['period'] == period]
        events = list(dict.fromkeys(events).keys())
        # result = events.copy()
        # frames=[s['frame'] for s in shifts]
        map=[t[1] for t in events] #initially, times for frames with an event are in the map
        # map = list(dict.fromkeys(map).keys()) # Remove duplicates
        # ctr=0
        for s,e in zip(events[:-1],events[1:]):
            if e[0] - s[0] > 1:
                times = np.linspace(s[1], e[1], e[0] - s[0] + 1)[1:-1] #Remove first and last since they are already in the map.
                map = map + list(times)
        # frames = [f for f in range(events[0][0], events[-1][0])]
        map = [float(v) for v in map]
        map.sort()
        full_map[period] = map
    target_file = os.path.join(source_dir, f"frame_time_maps",f"{game_id}.json" )
    print(f"Storing map for game {game_id}")
    with open(target_file,"w") as f:
        json.dump(full_map, f, indent=4)
    #return full_map



def download_shifts(game_ids, target_dir):
    req = login()
    ctr = 0
    for game_id in game_ids:
        ctr = ctr + 1
        print(f"{ctr} / {len(game_ids)}")
        try:
            response = req.get(API_URL + f'/v1/hockey/games/{game_id}/events/shifts')
            with open(os.path.join(target_dir, f"{game_id}.json"), "w") as f:
                json.dump(response.json(), f, indent=4)
                # f.write(response.text)
        except:
            print(f"Failed to download {game_id}")

def download_rosters(game_ids, target_dir):
    req = login()
    ctr = 0
    for game_id in game_ids:
        ctr = ctr + 1
        print(f"{ctr} / {len(game_ids)}")
        try:
            response = req.get(API_URL + f'/v1/hockey/games/{game_id}/roster')
            with open(os.path.join(target_dir, f"{game_id}.json"), "w") as f:
                json.dump(response.json(), f, indent=4)
                # f.write(response.text)
        except:
            print(f"Failed to download {game_id}")

def download_events(games, target_dir):
    SPORTLOGIQ_USERNAME = os.getenv('SPORTLOGIQ_USERNAME')
    SPORTLOGIQ_PWD = os.getenv('SPORTLOGIQ_PWD')
    #username = 'veronica.eriksson580@gmail.com' #your email address
    #password = 'B1llyfjant.1'
    apiurl = 'https://api.sportlogiq.com'

    login_payload = {'username': SPORTLOGIQ_USERNAME, 'password': SPORTLOGIQ_PWD}

    # use requests.Session() to handle cookies for you
    req = requests.Session()
    res = req.post(apiurl + '/v1/hockey/login', json=login_payload)
    ctr = 0
    for gameid in games:
        ctr += 1
        print(f"Fetching {gameid} ({ctr} of {len(games)})")
        try:
            response = req.get(apiurl + f'/v1/hockey/games/{gameid}/events/full')
            # response = api_request(url)
            with open(os.path.join(target_dir, f"{gameid}.json"), "w") as f:
                json.dump(response.json(), f, indent=4)
                # f.write(response.text)
        except:
            print(f"Failed to download {gameid}")
        # session cookies will be sent with subsequent calls to the API


def download_events_compiled(games, target_dir):
    SPORTLOGIQ_USERNAME = os.getenv('SPORTLOGIQ_USERNAME')
    SPORTLOGIQ_PWD = os.getenv('SPORTLOGIQ_PWD')
    #username = 'veronica.eriksson580@gmail.com' #your email address
    #password = 'B1llyfjant.1'
    apiurl = 'https://api.sportlogiq.com'

    login_payload = {'username': SPORTLOGIQ_USERNAME, 'password': SPORTLOGIQ_PWD}

    # use requests.Session() to handle cookies for you
    req = requests.Session()
    res = req.post(apiurl + '/v1/hockey/login', json=login_payload)
    ctr = 0
    for gameid in games:
        ctr += 1
        print(f"Fetching {gameid} ({ctr} of {len(games)})")
        try:
            response = req.get(apiurl + f'/v1/hockey/games/{gameid}/events/compiled')
            # response = api_request(url)
            with open(os.path.join(target_dir, f"{gameid}.json"), "w") as f:
                json.dump(response.json(), f, indent=4)
                # f.write(response.text)
        except:
            print(f"Failed to download {gameid}")
        # session cookies will be sent with subsequent calls to the API


def download_game_index(competition_id=1, season='20242025', stage='regular'):
    ROOTPATH = "/home/veronica/hockeystats/ver3"
    filepath = os.path.join(ROOTPATH, f"{competition_id}_{season}_{stage}.json")
    req = login()
    data = req.get(API_URL + f"/v1/hockey/games?season={season}&stage={stage}&competition_id={competition_id}&withvidparams=true")
    with open(f"{filepath}", "w") as f:
        json.dump(data.json(), f, indent=4)


def download_games(competition_id=17, season='20242025', stage='regular'):
    # Sames function as above. Deprecated.
    req = login()
    #response = req.get(API_URL + f'/v1/hockey/games/{game_id}/roster')
    #response = req.get(API_URL + f"/v1/hockey/games?competition_id={competition_id}&season_id={season}")
    response = req.get(API_URL + f"/v1/hockey/games?season={season}&stage={stage}&competition_id={competition_id}")
    #response = req.get(API_URL + f"/v1/hockey/games?competition_id=213&withvidparams=true")
    return response

def download_league_index():
    ROOTPATH = "/home/veronica/hockeystats/ver3"
    filepath = os.path.join(ROOTPATH, f"league_indexes.json")
    req = login()
    data = req.get(API_URL + f"/v1/hockey/competitions")
    with open(f"{filepath}", "w") as f:
        json.dump(data.json(), f, indent=4)

def download_players():
    print("apa")