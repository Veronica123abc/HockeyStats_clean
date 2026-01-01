import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import db_tools
import dotenv
import os
import ingest
import pandas as pd
# import entries
#from generate_entry_statistics import stats_db
import apiv2
dotenv.load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT")
import db_tools
from difflib import SequenceMatcher
from utils.data_tools import player_based_roster

def get_filepath(game_id):
    return f"/home/veronica/hockeystats/ver3/{game_id}"

def longest_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2)
    return match.find_longest_match(0, len(s1),0, len(s2)).size

def team_ids_from_name(game):
    # Extract the stored team_names and ids from database
    sl_game_id = game['id']
    events = game['events']
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    cursor.execute(f"select sl_homeTeamId, sl_awayTeamId  from game where sl_id={sl_game_id};")
    #cursor.execute(f"select home_team_id, away_team_id  from game where sl_id={sl_game_id};")
    team_ids = cursor.fetchall()[0]
    team_ids = [int(t) for t in team_ids]
    cursor.execute(f"select sl_displayName from team where id in {tuple(team_ids)};")
    team_names = [t[0] for t in cursor.fetchall()]

    # Extract teamnames from playsequence
    teams = list(set([k['team_in_possession'] for k in events]))
    teams = [t for t in teams if t]
    teams = [t for t in teams if t != 'None']
    if longest_substring(teams[0], team_names[0]) < longest_substring(teams[0], team_names[1]):
        teams_map =  {teams[0]:team_ids[0], teams[1]:team_ids[1]}
    else:
        teams_map = {teams[0]: team_ids[1], teams[1]:team_ids[0]}
    return teams_map

def get_roster(game_id, league='SHL'):
    roster = os.path.join(DATA_ROOT, f"{league}/rosters/{game_id}.json")
    with open(roster, "r") as file:
        roster = json.load(file)
    teams = list(roster.keys())
    player_info = []

    p_1 = [p for p in roster[teams[0]]['players']]
    for p in p_1:
        p.update({"team":teams[0]})
    player_info = player_info + p_1

    p_2 = [p for p in roster[teams[1]]['players']]
    for p in p_2:
        p.update({"team":teams[1]})
    player_info = player_info + p_2

    player_map = {p['id']: p for p in
                  player_info}  # {"id": player_id} f"{p['firsts_name']} {p['last_name']} {p['position']}"

    return player_map

def game_ids(leagues,seasons):
    game_ids = []
    for league in leagues:
        for season in seasons:
            with open(os.path.join(DATA_ROOT, f"leagues/{league}/{season}/games.json"), "r") as file:
                games = json.load(file)
            game_ids = game_ids + [g["id"] for g in games['games'] if g["stage"] != 'preseason']
    return game_ids



def get_game_dicts(game_id, ignore=None, filepath=None):
    if not ignore:
        ignore = []
    elif type(ignore) != list:
        ignore = [ignore]
    #if filepath is None:
    filepath = get_filepath(game_id)
    if os.path.exists(filepath):
        files = [os.path.join(filepath, f) for f in os.listdir(filepath) if f.endswith(".json") and f.replace(".json","") not in ignore]
    res = {}

    for file in files:
        try:
            with open(file, "r") as f:
                item = json.load(f)
        except:
            item = None
        item_name = os.path.basename(file).replace(".json", "")
        res[item_name] = item
    return res

