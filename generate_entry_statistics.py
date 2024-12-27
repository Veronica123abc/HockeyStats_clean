import mysql.connector
import mysql
import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher
#from sportlogiq import extract_game_info_from_schedule_html
import sportlogiq
import scraping
#import feature_engineering
import db_tools
import uuid
import logging
import entries_from_db
import entries

save_to_folder = './static/images'
#
# (t1, t2), teams = entries.generate_entry_statistics('/home/veronica/kalle.csv')#hockeystats/IIHF/U20/2023-24/playsequence-20230823-5 Nations Tournament U20-SLOvsSWE-20232024-107982.csv')
# plt = entries_from_db.oge_time_to_shot(t1)  # , bin_cnt=11, interval=3)
# print(teams[1])
# plt.title(f'Time to shot after entry for {teams[1]} at Even Strength', fontsize=30,
#           weight='bold')
# plt.figure(plt.get_fignums()[-1]).savefig(os.path.join(save_to_folder, teams[1]), dpi=100)
#

stats_db = db_tools.open_database()
cursor = stats_db.cursor()
sql = f"select team_id from participation where league_id=3 and season='2022-23';"
cursor.execute(sql)
teams=cursor.fetchall()
team_ids = [team[0] for team in teams]
team_ids=[65]

team_entries = entries_from_db.get_entries(4625, 65)
#oges = entries.time_entry_to_shot(df=team_entries, team=65)
for team_id in team_ids:
    team_name = db_tools.get_team_name(team_id)
    print('Analyzing entries for ', team_name, ' (',  team_ids.index(team_id), ' of ', len(team_ids), ')')
    #goals = db_tools.goals_in_game(830, manpower_situation='evenStrength')
    goals = db_tools.goals_in_season(team_id, league=3, season="2022-23", manpower_situation="evenStrength")
    entries = entries_from_db.generate_entry_statistics_team(team_id, 1, "2022-23")
    entry_goals = [e for e in entries if e['time_to_first_shot']]
    entry_goals = [e for e in entry_goals if e['time_to_first_shot'] <= 4.0]
    #es_goals = entries_from_db.es_goals_for_team(team_id, 3, '2022-23')
    es_goals = db_tools.goals_in_season(team_id, league=3, season="2022-23", manpower_situation="evenStrength")

    print('Team: ', team_name)
    print('Goals on entries: ', len(entry_goals))
    print('Even Strength goals: ', es_goals)
    print('Percent: ', round(100*float(float(len(entry_goals)) / float(es_goals['total'])),2))

    plt = entries_from_db.oge_time_to_shot(entries)#, bin_cnt=11, interval=3)
    plt.title(f'Time to shot after entry for {db_tools.get_team_name(team_id)} at Even Strength', fontsize=30, weight='bold')
    #annotation = f'Time to first shot after OZ Entry\n{team_name}\nEven Strength'
    #plt.text(5, 10, annotation, fontsize=30, fontweight='bold', color=[0.4,0.4,0.4,1.0])
    plt.figure(plt.get_fignums()[-1]).savefig(os.path.join(save_to_folder, db_tools.get_team_name(team_id)), dpi=100)
    # print(plt.get_fignums())
    # plt.show()
    #plt.show()
    #entries_from_db.generate_entry_graphics(entries, team_id, dir='static/images')
