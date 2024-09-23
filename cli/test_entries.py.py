import pandas as pd
import numpy as np
import cv2
import uuid
from utils.tools import *
import db_tools
from utils import read_write, graphics
from shapely.geometry import Polygon, Point
import entries
import geometry
import tkinter as tk
from tkinter import filedialog, constants, END
import tkinter
import copy
from PIL import Image, ImageTk
import pass_length
import json


team_id = 75;
league_id = 4
season = '2023-24'
stats_db = db_tools.open_database()
cursor = stats_db.cursor()
sql = f"select id from game where (home_team_id={team_id} or away_team_id={team_id}) and date > \'2023-07-01\';"
cursor.execute(sql)
games = cursor.fetchall()
game_ids = [g[0] for g in games]
game_statistics = []
# game_ids = [5963]
for idx, game_id in enumerate(game_ids):
    print(game_id)
    df = db_tools.get_events_from_game_with_team(game_id)
    oz_entries = entries.get_oz_rallies(df)
    teams = list(oz_entries.keys())
    if len(teams) != 2:
        continue

    selected_team = 0 if teams[0] == team_id else 1
    entry_times = {'team_1': entries.time_entry_to_shots(oz_entries[list(oz_entries.keys())[selected_team]]),
                   'team_2': entries.time_entry_to_shots(oz_entries[list(oz_entries.keys())[(selected_team + 1) % 2]])}

    game_statistics.append({'team_1': [e['rally_stat'] for e in entry_times['team_1']],
                            'team_2': [e['rally_stat'] for e in entry_times['team_2']]}
                           )
stats_team_1 = [x for xs in [g['team_1'] for g in game_statistics] for x in xs]
stats_team_2 = [x for xs in [g['team_2'] for g in game_statistics] for x in xs]

print(stats_team_1)