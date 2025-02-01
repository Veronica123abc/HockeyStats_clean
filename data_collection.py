#import mysql.connector
#import mysql
#import pandas as pd
#import numpy as  np
import os
from difflib import SequenceMatcher
from sportlogiq import extract_game_info_from_schedules, get_game_numbers_from_schedules
#import sportlogiq
import scraping

import db_tools
import uuid
#import logging
import json
import requests
import browser_cookie3

def verify_scores_schedules_gamefiles():
    games = extract_game_info_from_schedules("/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoffs/schedules")
    #goals = db_tools.goals_in_game(db_tools.get_game_id(sl_game_id=games[0]['sl_game_id']))
    errors = []
    for idx, game in []: #enumerate(games): #[13:14]:
        # print(game['sl_game_id'])
        goals = db_tools.goals_in_game(db_tools.get_game_id(sl_game_id=game['sl_game_id']))
        away_team_official = int(game['away_team_score'])
        home_team_official = int(game['home_team_score'])
        home_team_computed = goals[list(goals.keys())[0]]['total']
        away_team_computed = goals[list(goals.keys())[1]]['total']
        print(f"Game {idx}/{len(games)} Official score: {away_team_official} {home_team_official} Computed score: {away_team_computed} {home_team_computed} Total errors: {len(errors)}")
        #print(f"Computed score: {away_team_computed} {home_team_computed}")
        if away_team_computed != away_team_official or home_team_computed != home_team_official:
            # print(f"Error in game {game['sl_game_id']}")
            errors.append(game)
            print(errors)

def extract_games_from_db(query):
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()
    sql = query #f"select sl_game_id from game where league_id = 4 and date > \'2024-09-01\' and date < \'2024-12-13\';"
    cursor.execute(sql)
    games = cursor.fetchall()
    game_ids = [g[0] for g in games]
    return game_ids

def store_games_from_schedules(schedules_dir, league_id, competition_type='REG', teams_map=None):
    games = extract_game_info_from_schedules(schedules_dir)
    teams = [game['home_team'] for game in games] + [game['away_team'] for game in games]
    teams = list(set(teams))
    if teams_map is None:
        teams_map = db_tools.create_teamname_map(teams)
        print(teams_map)
        accept_teams_map = input("The scraped teamnames will be mapped to the teams in the database as shown above. Is this mapping correct?  (y/n): ")
        if accept_teams_map not in ['y', 'Y']:
            filename = f"team_names_map_{uuid.uuid4()}.json"
            print(f"Update the teammap stored as file {filename} and provide as input and run function again.")
            with open(filename,'w') as f:
                json.dump(teams_map, f)
            return None
    else:
        with open(teams_map) as f:
            teams_map = json.load(f)

    map = {map_item['sl_name']: map_item['id'] for map_item in teams_map}
    for game in games:
        game['home_team_id'] = int(map[game['home_team']])
        game['away_team_id'] = int(map[game['away_team']])
        game['type'] = competition_type
    # verify_scores_schedules_gamefiles()
    succeeded = []
    failed = []
    for game in games:
        print(game)
        stats_db = db_tools.open_database()
        cursor = stats_db.cursor()
        cursor.execute(f"select sl_game_id from game where sl_game_id = {game['sl_game_id']}")
        game_exists = len(cursor.fetchall()) > 0
        if not game_exists:
            sql = f"INSERT INTO game (home_team_id, away_team_id, date, league_id, type, sl_game_id, home_team_goals, away_team_goals, overtime, shootout) values " \
                  + f"({game['home_team_id']}, {game['away_team_id']}, '{game['date']}', {league_id}, '{game['type']}', {int(game['sl_game_id'])}, {int(game['home_team_score'])},{int(game['away_team_score'])}, {game['overtime']}, {game['shootout']});"
        else:
            sql = f"UPDATE game SET type='{game['type']}', home_team_goals={int(game['home_team_score'])}, away_team_goals={int(game['away_team_score'])}, overtime={game['overtime']}, shootout={game['shootout']} " \
                  + f"where sl_game_id = {game['sl_game_id']}"
        try:
            cursor.execute(sql)
            stats_db.commit()
            succeeded.append(game)

        except:
            print("Could not store the game. Already stored?")
            failed.append(game)

    return {'succeeded': succeeded, 'failed': failed}

def get_game_info():
    url=f"https://app.sportlogiq.com/api/v3/games?leagueid[]=13&seasonid[]=11&seasonstage[]=regular&withscores=true&withstates=true&withvidparams=true"

    def get_sportlogiq_cookies():
        cookies = browser_cookie3.chrome(domain_name="sportlogiq.com")  # or .firefox()
        cookie_dict = requests.utils.dict_from_cookiejar(cookies)
        return cookie_dict

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


def download_gamefile_api(game_id):

    # Function to extract cookies from Chrome (or Firefox)
    def get_sportlogiq_cookies():
        cookies = browser_cookie3.chrome(domain_name="sportlogiq.com")  # or .firefox()
        cookie_dict = requests.utils.dict_from_cookiejar(cookies)
        return cookie_dict

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
    url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv?xdbname=SHL"

    # Send the authenticated request
    session = requests.Session()
    response = session.get(url, headers=headers, cookies=cookies)

    # Print response
    print("Status Code:", response.status_code)
    try:
        print(response.json())  # Assuming JSON response
    except:
        print(response.text)
    with open(f"{game_id}.csv", "w") as f:
        f.write(response.text)

if __name__ == '__main__':
    get_game_info()
    download_gamefile_api(139067)
    league_file = '/home/veronica/hockeystats/IIHF/2023-24/league.html'
    schedules_dir = '/home/veronica/hockeystats/IIHF/2023-24/regular-season/schedules'
    games_dir = '/home/veronica/hockeystats/IIHF/2023-24/regular-season/gamefiles'

    import requests

    import requests
    import browser_cookie3


    # Function to extract cookies from Chrome (or Firefox)
    def get_sportlogiq_cookies():
        cookies = browser_cookie3.chrome(domain_name="sportlogiq.com")  # or .firefox()
        cookie_dict = requests.utils.dict_from_cookiejar(cookies)
        return cookie_dict


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
    url = "https://app.sportlogiq.com/api/0.2/games/139067/playsequence/csv?xdbname=SHL"

    # Send the authenticated request
    session = requests.Session()
    response = session.get(url, headers=headers, cookies=cookies)

    # Print response
    print("Status Code:", response.status_code)
    try:
        print(response.json())  # Assuming JSON response
    except:
        print(response.text)
    with open("a.csv","w") as f:
        f.write(response.text)
    print("apa")
    # game_ids = scraping.get_all_game_numbers(schedules_dir)
    # sql = f"select sl_game_id from game where league_id = 4 and date > \'2024-09-01\' and date < \'2025-01-11\';"
    # game_ids = extract_games_from_db(sql)
    # game_ids = [g for g in game_ids if str(g) not in [filename[:6] for filename in os.listdir("/home/veronica/hockeystats/Hockeyallsvenskan/2024-25/regular-season/gamefiles")]]
    # scraping.download_gamefiles(game_ids, src_dir=games_dir)

    # teams = scraping.extract_teams_from_league(league_file)
    # print(teams)
    # map = db_tools.create_teamname_map(teams)
    # print(map)
    # #teams = db_tools.load_teams_from_file('tmp/map.json')
    # for team in teams:
    #     t = db_tools.get_team_from_sl_id(team['sl_id'])
    #     print(team['sl_name'], " " , team['sl_id'], " ", t)
    # new_teams = db_tools.find_new_teams(teams)
    # teams = db_tools.create_teamname_map(teams)
    # print(teams)
    # db_tools.store_teams(teams)
    # db_tools.assign_teams(map, '2023-24', 3)

    # scraping.download_all_schedules(league_file, target_dir=schedules_dir, regular_season=True)
    # scraping.download_schedule("https://hockey.sportlogiq.com/teams/1576/schedule/all", path=schedules_dir, regular_season=True)

    # games = scraping.get_all_game_numbers(schedules_dir)
    # print(games)
    # store_games_from_schedules(schedules_dir, 3, 'REG', teams_map=None)#"team_names_map_640dace7-a24d-4711-b67d-7f99b5dd604e")
    # verify_scores_schedules_gamefiles()

    # root_dir='/home/veronica/hockeystats/IIHF/2020-21/regular-season/gamefiles'
    # files = os.listdir(root_dir)
    # for file in [os.path.join(root_dir,f) for f in files]:
    #     db_tools.store_players(file)

    # ctr = 0
    # for file in [os.path.join(root_dir,f) for f in files]: #[470:]:
    #     print(f"{ctr} of {len(files)} {file}")
    #     db_tools.store_events(file)
    #     ctr += 1

    #game_number = 1
    #entries.line_toi_when_goal(game_number)