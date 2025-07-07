#import mysql.connector
#import mysql
#import pandas as pd
#import numpy as  np
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

def get_sportlogiq_cookies():
    cookies = browser_cookie3.chrome(domain_name="sportlogiq.com")  # or .firefox()
    cookie_dict = requests.utils.dict_from_cookiejar(cookies)
    return cookie_dict

def get_game_info():
    url=f"https://app.sportlogiq.com/api/v3/games?leagueid[]=13&seasonid[]=11&seasonstage[]=regular&withscores=true&withstates=true&withvidparams=true"

    # def get_sportlogiq_cookies():
    #     cookies = browser_cookie3.chrome(domain_name="sportlogiq.com")  # or .firefox()
    #     cookie_dict = requests.utils.dict_from_cookiejar(cookies)
    #     return cookie_dict

        # Extract cookies from the authenticated browser session

    cookies = get_sportlogiq_cookies()

    # Define headers (similar to what the browser sends)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "text/plain",
        "Host": "app.sportlogiq.com",
        "Origin": "https://hockey.sportlogiq.com",
        "Referer": "https://hockey.sportlogiq.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    }

    # API URL

    # Send the authenticated request
    session = requests.Session()
    response = session.get(url, headers=headers, cookies=cookies)

    # Print response
    print("Status Code:", response.status_code)
    try:
        print(response.json())  # Assuming JSON response
    except:
        print(response.text)
    with open("gameinfo.txt", "w") as f:
        f.write(response.text)

def download_gamefiles_api(game_ids, target_dir='/home/veronica/hockeystats/IIHF/all_seasons/gamefiles/json'):
    ctr = 0
    for game_id in game_ids:
        url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv"
        url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playerevents"
        ctr += 1
        print(f"Fetching {game_id} ({ctr} of {len(game_ids)})")
        try:
            response = api_request(url)
            with open(os.path.join(target_dir, f"{game_id}.json"), "w") as f:
                json.dump(response.json(), f, indent=4)
                #f.write(response.text)
        except:
            print(f"Failed to download {game_id}")


def download_players_api(league_id, season_id, season_stage='regular'):

    url = f"https://app.sportlogiq.com/api/0.2/leagues/{league_id}/seasons/{season_id}/stage/{season_stage}/players"
    res = api_request(url)
    json_object = res.json()
    filename = f"/home/veronica/hockeystats/{json_object['leaguename']}/{json_object['seasonname']}/players.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename,"w") as f:
        json.dump(res.json(), f, indent=4)



def download_games_api(league_id, season_id, season_stage='regular'):
    print("apa")
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()
    sql = f"select name, sl_id from league where id={league_id};"
    print(sql)
    cursor.execute(sql)
    print("apa")
    league_name, sl_league_id = cursor.fetchall()[0]

    url=f"https://app.sportlogiq.com/api/v3/games?leagueid[]={sl_league_id}&seasonid[]={season_id}&seasonstage[]={season_stage}&withstates=true&withscores=true&withvidparams=true&withreferences=true"
    res = api_request(url)
    json_object = res.json()
    return json_object
    filename = f"/home/veronica/hockeystats/{league_name}/{json_object['seasonname']}/games_{season_stage}.json"
    with open(filename) as f:
        json.dump(json_object, f, indent=4)

def download_full_game_stats(game_id, target_dir="./tmp"):
    with open("sportlogiq_definitions/full_report_metrics.json","r") as f:
        metrics = json.load(f)
    #metric_ids = [int(k['id']) for k in [q['metrics'] for q in metrics['metricSets']]]
    metric_ids = []
    for k in metrics['metricSets']:
        for l in k['metrics']:
            metric_ids.append(l['id'])
    ctr=1;
    for metric in metric_ids:
        print(f"Metric {ctr} of {len(metric_ids)}")
        res = api_request(url=f"https://app.sportlogiq.com/api/0.2/games/{game_id}/reportmetrics/{metric}/postgame/player?")
        with open(f"{target_dir}/{game_id}_{metric}.json","w") as f:
            json.dump(res.json(), f, indent=4)
        ctr += 1

def api_request(url, payload=None):
    # Function to extract cookies from Chrome (or Firefox)
    # Extract cookies from the authenticated browser session
    cookies = get_sportlogiq_cookies()

    # Define headers (similar to what the browser sends)
    headers = {
        "Accept": "application/json, text/plain, */*",
        #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "text/plain",
        "Host": "app.sportlogiq.com",
        #"Host": "media11.sportlogiq.com",
        "Origin": "https://hockey.sportlogiq.com",
        "Referer": "https://hockey.sportlogiq.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    }

    headers_video = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-mpegURL",
        "Host": "app.sportlogiq.com",
        "Origin": "https://hockey.sportlogiq.com",
        "Referer": "https://hockey.sportlogiq.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    }

    # API URL
    #url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv?xdbname=SHL"

    # Send the authenticated request
    session = requests.Session()
    if payload:
        response = session.post(url, json=payload, headers=headers, cookies=cookies)
    else:
        response = session.get(url, headers=headers, cookies=cookies)

    # Print response
    print("Status Code:", response.status_code)

    # try:
    #     print(response.json())  # Assuming JSON response
    # except:
    #     print(response.text)
    # # with open(f"{game_id}.csv", "w") as f:
    # #     f.write(response.text)
    return response
