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

def scoring_chances(game_data):
    game_info = game_data['game-info']
    playsequence = game_data['playsequence']

    home_team_name = f"{game_info['home_team']['location']} {game_info['home_team']['name']}"
    away_team_name = f"{game_info['away_team']['location']} {game_info['away_team']['name']}"

    a_chances_home_team = [(p['game_time'], 'A') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'A' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == home_team_name]
    a_chances_away_team = [(p['game_time'], 'A') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'A' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == away_team_name]
    b_chances_home_team = [(p['game_time'], 'B') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'B' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == home_team_name]
    b_chances_away_team = [(p['game_time'], 'B') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'B' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == away_team_name]
    c_chances_home_team = [(p['game_time'], 'C') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'C' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == home_team_name]
    c_chances_away_team = [(p['game_time'], 'C') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'C' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == away_team_name]

    return {'home_team': a_chances_home_team + b_chances_home_team + c_chances_home_team,
            'away_team': a_chances_away_team + b_chances_away_team + c_chances_away_team}

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

def number_goals(df, team_name, manpower_situation='5v5'):
    num_goals = df[(df['name'] == 'goal') & (df['team_in_possession'] == team_name) &
                         (df['team_skaters_on_ice'] == 5) &
                         (df['opposing_team_skaters_on_ice'] == 5)]

    return num_goals