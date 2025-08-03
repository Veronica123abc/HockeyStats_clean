import json
import matplotlib.pyplot as plt
import matplotlib.patches as matches
from collections import defaultdict
import db_tools
import dotenv
import os
import ingest
import pandas as pd
import numpy as np
# import entries
#from generate_entry_statistics import stats_db
import apiv2
dotenv.load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT")



def add_team_id_to_game_info(playsequence, roster, game_info):
    teams = list(set([a['team_in_possession'] for a in playsequence['events'] if (a['team_in_possession'] is not None) and (not a['team_in_possession'] == 'None')]))
    player_id = [p['team_forwards_on_ice_refs'] for p in playsequence['events'] if p['team_in_possession'] == teams[0]][0][0]
    player_team = roster[player_id]['team']

    if game_info['home_team']['id'] == player_team:
        game_info['ps_home_team_name'] = teams[0]
        game_info['ps_away_team_name'] = teams[1]
    else:
        game_info['ps_home_team_name'] = teams[1]
        game_info['ps_away_team_name'] = teams[0]

    return game_info

def player_based_roster(roster):
    teams = list(roster.keys())
    player_info = []

    p_1 = [p for p in roster[teams[0]]['players']]
    for p in p_1:
        p.update({"team": teams[0]})
    player_info = player_info + p_1

    p_2 = [p for p in roster[teams[1]]['players']]
    for p in p_2:
        p.update({"team": teams[1]})
    player_info = player_info + p_2

    player_map = {p['id']: p for p in
                  player_info}  # {"id": player_id} f"{p['firsts_name']} {p['last_name']} {p['position']}"

    return player_map