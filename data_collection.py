
import numpy as  np
import os
from difflib import SequenceMatcher

import visualizations
from sportlogiq import extract_game_info_from_schedules, get_game_numbers_from_schedules


import db_tools
import uuid

import json
import api
import re
import requests
import apiv2
from apiv2 import apiv2 as api2

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

def download_gamefiles_api(game_ids, target_dir='./tmp'):
    for game_id in game_ids:
        url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv"
        url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence"
        response = api_request(url)

        with open(f"{game_id}.csv", "w") as f:
            f.write(response.text)

def download_players_api(league_id, season_id, season_stage='regular'):

    url = f"https://app.sportlogiq.com/api/0.2/leagues/{league_id}/seasons/{season_id}/stage/{season_stage}/players"
    res = api_request(url)
    json_object = res.json()
    filename = f"/home/veronica/hockeystats/{json_object['leaguename']}/{json_object['seasonname']}/players.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename,"w") as f:
        json.dump(res.json(), f, indent=4)



def download_games_api(league_id, season_id, season_stage='regular'):
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()
    sql = f"select name, sl_id from league where id={league_id};"
    cursor.execute(sql)

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
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "text/plain",
        "Host": "app.sportlogiq.com",
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
    try:
        print(response.json())  # Assuming JSON response
    except:
        print(response.text)
    # with open(f"{game_id}.csv", "w") as f:
    #     f.write(response.text)
    return response

def create_url_seasons(seasons):
    season_string = [f"seasonid[]={s}" for s in seasons]
    return "&".join(season_string)

def fetch_all_games():
    all_leagues = json.load(open("sportlogiq_definitions/all_leagues_full.json", "r"))
    leagues = [int(k['id']) for k in all_leagues]
    for league in leagues[70:]:
        leagueid=league['id']
        res = api.api_request(f"https://app.sportlogiq.com/api/v3/games?leagueid[]={leagueid}&withscores=true&withreferences=true")
        folder = re.sub('\\\\\'','_', league['name'])
        folder = re.sub(' ','_',folder)
        path = os.path.join("/home/veronica/hockeystats/ver2",folder, f"all_games_{leagueid}.json")
        json.dump(res.json(), open(path,"w"), indent=4)
        print(league['name'])

def fetch_all_players(league_id, seasons):
    season_string = create_url_seasons(seasons)
    all_leagues = json.load(open("sportlogiq_definitions/all_leagues_full.json", "r"))
    league_name = [k['name'] for k in all_leagues if k['id']==str(league_id)][0]
    url = f"https://app.sportlogiq.com/api/v3/players?leagueid[]={league_id}&{season_string}&seasonstage[]=regular&seasonstage[]=playoffs&withseasonsummaries=true&withstatuses=true&withreferences=true"
    print("fetching from league ", league_name)
    res = api.api_request(url=url)
    folder = re.sub('\\\\\'', '_', league_name)
    folder = re.sub(' ', '_', folder)
    path = os.path.join("/home/veronica/hockeystats/ver2", folder, f"all_players_{league_id}.json")
    print("Storing results in", path)
    json.dump(res.json(), open(path, "w"), indent=4)


def get_frame_to_time(game_id, source_dir, league='SHL'):
    full_events = json.load(open(os.path.join(source_dir,league,"playsequences", f"{game_id}.json")))
    #shifts = json.load(open(f"{source_dir}/shifts/{game_id}.json","r"))
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
        map = map + 1000 * [map[-1]]  # quickfix to avoid reading out of list.
        period_item = {}
        period_item['first_frame'] = events[0][0]
        period_item['period_time'] = map
        full_map[period] = period_item
    return full_map


def get_frame_to_time_hack(full_events):

    #shifts = json.load(open(f"{source_dir}/shifts/{game_id}.json","r"))
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
        map = map + 1000 * [map[-1]]  # quickfix to avoid reading out of list.
        period_item = {}
        period_item['first_frame'] = events[0][0]
        period_item['period_time'] = map
        full_map[period] = period_item
    return full_map

def add_shift_times_hack(shifts, events):
    #print(f"Adding times for shifts in {game_id}")
    map = get_frame_to_time_hack(events)
    new_shifts=[]
    for shift in shifts:
        #print(shift)
        period_map = map[shift['period']]
        first_frame = period_map['first_frame']
        # print(period_map['period_time'])
        # print(shift['frame'])
        #try:
        shift['period_time'] = period_map['period_time'][shift['frame'] - first_frame]
        #except:
        #    print("apa")
        new_shifts.append(shift)
    return new_shifts
    #print(shifts)


def add_shift_times(game_id, source_dir, league='SHL'):
    print(f"Adding times for shifts in {game_id}")
    map = get_frame_to_time(game_id, source_dir, league=league)
    shifts = json.load(open(os.path.join(source_dir, league, f"shifts/{game_id}.json")))
    new_shifts=[]
    for shift in shifts:
        #print(shift)
        period_map = map[shift['period']]
        first_frame = period_map['first_frame']
        shift['period_time'] = period_map['period_time'][shift['frame'] - first_frame]
        new_shifts.append(shift)
    with open(os.path.join(source_dir, f"{league}", f"shifts/{game_id}.json"),"w") as f:
        json.dump(new_shifts,f,indent=4)
    #print(shifts)

def verify_players():
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    sql = f"select sl_id from game where sl_leagueId=213;"
    cursor.execute(sql)
    game_ids = [g[0] for g in cursor.fetchall()]

    all_players = []
    all_stored_players = []
    for game in game_ids:
        path = f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/{game}.json"
        events = json.load(open(path,"r"))
        players = [k['player_reference_id'] for k in events['events']]
        players = list(set(players))
        players = [int(p) for p in players if p is not None]
        sql = f"select sl_id from player where sl_id in {tuple((p for p in players))};"
        cursor.execute(sql)
        stored_players = [p[0] for p in cursor.fetchall()]
        missing = [p for p in players if p not in stored_players]
        print(missing)
        if len(missing) >0:
            print("apa")
        print(f"{len(stored_players)}, {len(players)}")
        #all_players = list(set(all_players + players))
        #all_stored_players = list(set(all_stored_players + stored_players))




def download_complete_game(game_id, game_info=True, roster=True, playsequence=True, playsequence_compiled=True, shifts=True, update=True):
    ROOTPATH = "/home/veronica/hockeystats/ver3"
    filepath = os.path.join(ROOTPATH, str(game_id))
    if not (os.path.exists(filepath) and os.path.isdir(filepath)):
        os.makedirs(filepath)

    conn = api2()
    if game_info:
        print("Fetching gameinfo")
        data = conn.get_game_info(game_id)
        with open(f"{filepath}/game-info.json", "w") as f:
            json.dump(data.json(), f, indent=4)
    if roster:
        print("Fetching rosters")
        data = conn.get_roster(game_id)
        with open(f"{filepath}/roster.json", "w") as f:
            json.dump(data.json(), f, indent=4)
    if playsequence:
        print("Fetching events")
        data = conn.get_events(game_id)
        events = data.json()
        with open(f"{filepath}/playsequence.json", "w") as f:
            json.dump(data.json(), f, indent=4)
    if playsequence_compiled:
        print("Fetching compiled events")
        data = conn.get_compiled_events(game_id)
        with open(f"{filepath}/playsequence_compiled.json", "w") as f:
            json.dump(data.json(), f, indent=4)
    if shifts:
        print("Fetching shifts")
        data = conn.get_shifts(game_id)
        data = add_shift_times_hack(data.json(), events)

        with open(f"{filepath}/shifts.json", "w") as f:
            json.dump(data, f, indent=4)

def download_complete_games(game_index_file):
    ROOTPATH = "/home/veronica/hockeystats/ver3"

    j = json.load(open(game_index_file))
    #j = json.load(open(f"/home/veronica/hockeystats/ver3/game_indexes/1_20242025_regular.json", "r"))

    game_ids = [g['id'] for g in j['games']]
    new_game_ids = []
    for game_id in game_ids:
        filepath = os.path.join(ROOTPATH, str(game_id))
        if (os.path.exists(filepath) and os.path.isdir(filepath)):
            existing_files = [os.path.join(ROOTPATH,str(game_id), f) for f in os.listdir(filepath)]
            correct_existing_files = [f for f in existing_files if os.stat(f).st_size > 0]
            if len(correct_existing_files) != 5:
                new_game_ids.append(game_id)
        else:
            new_game_ids.append(game_id)

    failed = []
    ctr = 0
    for game_id in new_game_ids:
        ctr += 1
        print(f"Trying to download {ctr} of {len((new_game_ids))}")
        try:
            download_complete_game(game_id)
            print(f"Succeeded {game_id}")
        except:
            print(f"Failed {game_id}")

    #apiv2.download_rosters(game_id,target_dir=filepath)
    #apiv2.download_shifts(game_ids[340:], target_dir='/home/veronica/hockeystats/ver2/SHL/shifts')
    #apiv2.download_events(game_ids,f"/home/veronica/hockeystats/ver2/SHL/playsequences")
    #apiv2.download_events_compiled(game_ids, f"/home/veronica/hockeystats/ver2/SHL/playsequences_compiled")


if __name__ == '__main__':



    #print("apa")
    a=apiv2.download_game_index(competition_id=1, season='20242025', stage='playoffs')
    exit(0)
    download_complete_games("/home/veronica/hockeystats/ver3/game_indexes/1_20242025_regular.json")
    exit(0)
    #download_complete_games(f"/home/veronica/hockeystats/ver2/SHL/all_games_13.json")
    #j=json.load(open(f"/home/veronica/hockeystats/ver2/SHL/all_games_13.json","r"))
    #game_ids=[k['id'] for k in j['games'] if k['seasonId']=='11']

    #apiv2.download_rosters(game_ids,target_dir='/home/veronica/hockeystats/ver2/SHL/rosters')
    #apiv2.download_shifts(game_ids[340:], target_dir='/home/veronica/hockeystats/ver2/SHL/shifts')
    #apiv2.download_events(game_ids,f"/home/veronica/hockeystats/ver2/SHL/playsequences")
    # apiv2.download_events_compiled(game_ids, f"/home/veronica/hockeystats/ver2/SHL/playsequences_compiled")
    exit(0)

    #shifts = visualizations.process_shifts("/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/shifts/137440.json")
    #toi = visualizations.current_shift_time_on_ice(shifts, 254.2)
    #verify_players()


    # b=os.listdir("/home/veronica/hockeystats/ver2/SHL/shifts")
    # game_ids = [int(os.path.splitext(k)[0]) for k in b if os.path.splitext(k)[0].isnumeric()]
    # for game_id in game_ids:
    #     add_shift_times(game_id, "/home/veronica/hockeystats/ver2")
    # exit(0)
    # apiv2.download_rosters(game_ids,target_dir='/home/veronica/hockeystats/ver2/IIHF_World_Championship/rosters')
    # apiv2.download_shifts(game_ids, target_dir='/home/veronica/hockeystats/ver2/IIHF_World_Championship/shifts')

    game_ids = [g['id'] for g in j['games']]
    #req = requests.Session()
    apiurl = "https://api.sportlogiq.com"
    req = apiv2.login()
    for g in game_ids[200:300]:
        print(g)
        r = req.get(apiurl + f'/v1/hockey/games/{g}/playerTOI')
        print("apa")
    apiv2.download_events(game_ids, target_dir="/home/veronica/hockeystats/ver2/test")
    #api.download_gamefiles_api(game_ids, target_dir='/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences')
    exit(0)
    apiv2.test()
    for i in range(0,0):#240):
        num_digits = len(str(i))
        padding="0"*(4-num_digits)
        clip =padding+str(i)
        url = f"https://media11.sportlogiq.com/141655/141655-3_{clip}.ts?auth=AAAAILtxhtaN3rNMglO3CJM61MpXBpg8pi~b7QW6z899l2MleyJ1IjoiMTE2NDQiLCJzIjoiaCIsImciOiIxNDE2NTUiLCJ4IjoiMjAyNS0wMy0yMlQyMDoxOToxNiJ9"
        res = api.api_request(url) #, payload="auth=AAAAILtxhtaN3rNMglO3CJM61MpXBpg8pi~b7QW6z899l2MleyJ1IjoiMTE2NDQiLCJzIjoiaCIsImciOiIxNDE2NTUiLCJ4IjoiMjAyNS0wMy0yMlQyMDoxOToxNiJ9")
        #session = requests.Session()
        #session.get(url)
        print(i)
    apiurl = "https://api.sportlogiq.com"
    gameid =  141655
    req = requests.Session()
    ev = req.get(apiurl + f'/v1/hockey/games/{gameid}/events/full')
    #ev = pd.DataFrame(ev.json()['events'])
    fetch_all_players(17,[11])
    #res = api.api_request("https://app.sportlogiq.com/api/v3/playershifts2?leagueid=17&seasonid=11&seasonstage=regular&from=2024-09-20T16:00:00.000Z&to=2025-02-14T18:00:00.000Z&playerid[]=7698&withvidparams=true&includeshiftsentrycomplete=true")
    #season_string = create_url_seasons([6,7,8,9,10,11])
    #url = f"https://app.sportlogiq.com/api/v3/players?leagueid[]={213}&{season_string}&seasonstage[]=regular&seasonstage[]=playoffs&withseasonsummaries=true&withstatuses=true&withreferences=true"
    #res = api.api_request(url=url)
    #json.dump(open("/home/veronica/hockeystats/ver2/IIHF_World_Championship/all_players_213.json"))
    ##p=json.load(open("sportlogiq_definitions/all_games_13.json","r"))
    #leagues = json.load(open("sportlogiq_definitions/all_leagues_full.json", "r"))
    league_ids = [k['id'] for k in leagues]
    for league_id in league_ids[42:]:
        if league_id !="213":
            fetch_all_players(league_id, seasons=[6,7,8,9,10,11])
    payload = {
        "leagueid": [1],
        "seasonid": [11],
        "playerid": list(range(1, 1001)),  # Example: 1,000 players
        "withtoi": True
    }
    #res = api.api_request(f"https://app.sportlogiq.com/api/v3/teams?withreferences=true")
    #print(res)
    #leagues=[int(k['id']) for k in p]
    # for league in leagues[70:]:
    #     leagueid=league['id']
    #     res = api.api_request(f"https://app.sportlogiq.com/api/v3/games?leagueid[]={leagueid}&withscores=true&withreferences=true")
    #     folder = re.sub('\\\\\'','_', league['name'])
    #     folder = re.sub(' ','_',folder)
    #     path = os.path.join("/home/veronica/hockeystats/ver2",folder, f"all_games_{leagueid}.json")
    #     json.dump(res.json(), open(path,"w"), indent=4)
    #     print(league['name'])
    #res = api_request(url=f"https://app.sportlogiq.com/api/v3/players?leagueid[]=1&seasonid[]=10&seasonstage[]=regular&withseasonsummaries=true&withstatuses=true&withreferences=true")
    res = api_request(url=f"https://app.sportlogiq.com/api/v3/players?leagueid[]=1&seasonid[]=10&seasonid[]=9&seasonstage[]=regular&seasonstage[]=playoffs&withseasonsummaries=true&withstatuses=true&withreferences=true")
    #res = api_request(url=f"https://app.sportlogiq.com/api/v3/players?leagueid[]=1&withseasonsummaries=true&withstatuses=true&withreferences=true")


    api.download_players_api(213,7,'regular')
    res = api.download_games_api(1,10,'regular')
    #download_players_api(league_id=13, season_id=11, season_stage='regular')

    #get_game_info()
    #download_gamefile_api(139067)
    game_id = 139067
    game_id = 137436
    game_id = 110494
    download_games_api(1,8,'regular')
    # url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv?xdbname=SHL"
    # res=api_request(url)
    # leagues = scraping.extract_all_leagues("sportlogiq_definitions/all_leagues.txt")
    # download_gamefiles_api([game_id])
    # res = api_request("https://media11.sportlogiq.com/143400/143400-1_0000.ts?auth=AAAAIGAfvmBTp4k5rYmybGZFCC1z021XjEJEyjjCOqDAst30eyJ1IjoiMTE2NDQiLCJzIjoiaCIsImciOiIxNDM0MDAiLCJ4IjoiMjAyNS0wMy0wM1QyMTozOTozNSJ9")
    #api_request(url = f"https://app.sportlogiq.com/api/0.2/games/{game_id}/playsequence/csv?xdbname=SHL")
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
        with open(f"game_metrics/{game_id}_{metric}.json","w") as f:
            json.dump(res.json(), f, indent=4)
        ctr += 1
    res = api_request(url = f"https://app.sportlogiq.com/api/0.2/games/143400/reportmetrics/18838/postgame/player?")
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