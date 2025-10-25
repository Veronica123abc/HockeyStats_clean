import json
import dotenv
import os
import time
from utils import file_tools #team_ids_from_name
# import entries
#from generate_entry_statistics import stats_db
import matplotlib.pyplot as plt

import db_tools
import pandas as pd
from tqdm import tqdm

from tqdm import tqdm
from collections import defaultdict
import data_collection
from utils.shifts import shift_data, process_shifts, shifts_reset_on_whistle, current_shift_time_on_ice
from utils.data_tools import add_team_id_to_game_info
from utils import data_tools
import numpy as np


# def shots_on_net(games, team_name=None):
#     ctr = 0
#     for game in games:
#         ctr += 1
#         print(f"Game {game} ({ctr} of {len(games)})")
#
#         game_data = file_tools.get_game_dicts(game, ignore='playsequence_compiled')
#         game_info = game_data['game-info']
#         df = pd.DataFrame.from_records(game_data['playsequence']['events'])
#         home_team = f"{game_info['home_team']['location']} {game_info['home_team']['name']}"
#         away_team = f"{game_info['away_team']['location']} {game_info['away_team']['name']}"
#
#         res_home_team = slot_shot_stats(df, home_team)
#         res_away_team = slot_shot_stats(df, away_team)
#
#         print(res_home_team)
#         print(res_away_team)

def dashboard_1(games, team_id, per_goal=True):
    team_stats = defaultdict(list)
    for game in tqdm(games):
        res = shots_on_net(game, per_goal=per_goal)
        for r in res:
            team_stats[r[0]].append(r[1])
    res = dashboard_1_aggregate(team_stats[team_id])
    print(res)

def dashboard_1_aggregate(stats):
    goals = sum([v['goals'] for v in stats])
    res = {}
    if goals == 0:
        return None
    res['all_slot_shot_attempts'] = round(sum([v['all_slot_shot_attempts'] / goals for v in stats]), 2)
    res['all_slot_shots_onnet'] = round(sum([v['all_slot_shots_onnet'] / goals for v in stats]), 2)
    res['inner_slot_shot_attempts'] = round(sum([v['inner_slot_shot_attempts'] / goals for v in stats]), 2)
    res['inner_slot_shots_onnet'] = round(sum([v['inner_slot_shots_onnet'] / goals for v in stats]), 2)
    res['A'] = round(sum([v['A'] / goals for v in stats]),2)
    res['B'] = round(sum([v['B'] / goals for v in stats]), 2)
    res['C'] = round(sum([v['C'] / goals for v in stats]), 2)
    res['ABC'] = round(sum([(v['A'] + v['B'] + v['C']) / goals for v in stats]), 2)

    return res



def shots_on_net(game, per_goal=True):

    game_data = file_tools.get_game_dicts(game, ignore='playsequence_compiled')
    game_info = game_data['game-info']
    df = pd.DataFrame.from_records(game_data['playsequence']['events'])
    home_team_id = game_info['home_team']['id']
    away_team_id = game_info['away_team']['id']
    home_team_name = f"{game_info['home_team']['location']} {game_info['home_team']['name']}"
    away_team_name = f"{game_info['away_team']['location']} {game_info['away_team']['name']}"

    res = [
        (home_team_id, slot_shot_stats(df, home_team_name, per_goal=per_goal)),
        (away_team_id, slot_shot_stats(df, away_team_name, per_goal=per_goal))
    ]
    return res


def slot_shot_stats(df, team_name, per_goal=True):
    res = {}
    shots = df[(df['name'] == 'shot') &
               (df['team_in_possession'] == team_name) &
               (df['opposing_team_skaters_on_ice'] == 5) &
               (df['team_skaters_on_ice'] == 5)]#[['outcome', 'type', 'shorthand', 'play_section']]

    res['all_slot_shot_attempts'] = len(shots[shots['type'] == 'slot'])
    res['all_slot_shots_onnet'] = len(shots[(shots['type'] == 'slot') & (shots['outcome'] == 'successful')])
    res['inner_slot_shot_attempts'] = len(shots[(shots['type'] == 'slot') & (shots['play_section'] == 'innerSlot')])
    res['inner_slot_shots_onnet'] = len(shots[(shots['type'] == 'slot') &
                                              (shots['play_section'] == 'innerSlot') &
                                              (shots['outcome'] == 'successful')])
    res['goals'] = len(df[(df['name'] == 'goal') & (df['team_in_possession'] == team_name) & (
            df['team_skaters_on_ice'] == 5) & (df['opposing_team_skaters_on_ice'] == 5)])

    res['A'] = len(shots[shots['expected_goals_all_shots_grade'] == 'A'])
    res['B'] = len(shots[shots['expected_goals_all_shots_grade'] == 'B'])
    res['C'] = len(shots[shots['expected_goals_all_shots_grade'] == 'C'])

    if per_goal:
        res_w_per_goal = res
        goals = len(df[(df['name'] == 'goal') & (df['team_in_possession'] == team_name) & (
                    df['team_skaters_on_ice'] == 5) & (df['opposing_team_skaters_on_ice'] == 5)])
        #keys = res.keys()
        for k in list(res.keys()):
            res[k + '_per_goal'] = res[k] / goals if goals > 0 else -1
    return res


# def abc_chances_stats(df):
# shots = df[(df['name'] == 'shot') &
#                (df['team_in_possession'] == team_name) &
#                (df['opposing_team_skaters_on_ice'] == 5) &
#                (df['team_skaters_on_ice'] == 5)][['outcome', 'type', 'shorthand', 'play_section']]

# def slot_shot_stats(shots):
#     res = {}
#     res['all_slot_shot_attempts'] = len(shots[shots['type'] == 'slot'])
#     res['all_slot_shots_onnet'] = len(shots[(shots['type'] == 'slot') & (shots['outcome'] == 'successful')])
#     res['inner_slot_shot_attempts'] = len(shots[(shots['type'] == 'slot') & (shots['play_section'] == 'innerSlot')])
#     res['inner_slot_shots_onnet'] = len(shots[(shots['type'] == 'slot') &
#                                               (shots['play_section'] == 'innerSlot') &
#                                               (shots['outcome'] == 'successful')])
    return res

if __name__ == "__main__":
    #shots_on_net([15443])
    #shots_on_net(139172)
    games = data_collection.get_all_games('213', selected_seasons=['20242025'])
    sweden_games = [g['id'] for g in games if g['home_team_id'] == '1339' or g['away_team_id'] == '1339']
    dashboard_1(sweden_games, team_id='1339', per_goal=False)
