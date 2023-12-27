import mysql.connector
import mysql
import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher
import db_tools
import store_players
from sportlogiq import extract_game_info_from_schedule_html
import sportlogiq
import scraping
import feature_engineering
import db_tools
import uuid
import logging

def longest_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2)
    return match.find_longest_match(0, len(s1),0, len(s2)).size

def verify_teamnames(root_dir):
    files = [os.path.join(root_dir, file) for file in os.listdir(root_dir)]
    res=[]
    for file in files:
        print('Extracting games from ', file)
        games = extract_game_info_from_schedule_html(file)
        print(file,' ', len(games))
        for game in games:
            home_team_id = get_team_id_from_substring(game[0])  # get_team_id(game[0])
            away_team_id = get_team_id_from_substring(game[1])  # get_team_id(game[1])
            print(f"{game[0]} : {home_team_id}")
            print(f"{game[1]} : {away_team_id}")
            h = (home_team_id, game[0])
            a = (away_team_id, game[1])
            if h not in res:
                res.append(h)
            if a not in res:
                res.append(a)
        print(res)
        print('apa')

def store_game(game, league_id):

    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()

    home_team_id = get_team_id_from_substring(game[0]) #get_team_id(game[0])
    away_team_id = get_team_id_from_substring(game[1])  #get_team_id(game[1])

    sql = "INSERT INTO game (home_team_id, away_team_id, date, sl_game_id, league_id) values (%s, %s, %s, %s, %s)"
    values = (home_team_id, away_team_id, game[2], int(game[3]), int(league_id))
    try:
        cursor.execute(sql, values)
        stats_db.commit()
    except:
        print("Could not store the game. Already stored?")

def get_team_id_from_substring(team_name):
    all_teams = db_tools.get_all_teams()
    lls = 0
    team_id = -1
    for t in all_teams:
        team=t[1]
        ss = longest_substring(team, team_name)
        if ss > lls:
             team_id = t[0]
             lls = ss
    return team_id
def store_games(root_dir, league_id):
    files = [os.path.join(root_dir, file) for file in os.listdir(root_dir)]
    for file in files:
        print('Extracting games from ', file)
        games = extract_game_info_from_schedule_html(file)
        print(file,' ', len(games))
        for game in games:
            print('Storing: ', game)
            store_game(game, league_id)

if __name__ == '__main__':
    #league_file = '/home/veronica/hockeystats/shl-2023-24.txt'
    league_file = '/home/veronica/hockeystats/Hockeyallsvenskan/hockeyallsvenskan-2022-23.txt'
    schedules_dir = '/home/veronica/repos/HockeyStats/tmp/playoff'
    # teams = scraping.extract_teams_from_league(league_file)
    #db_tools.store_teams(teams)
    #db_tools.assign_teams(teams, season='2022-23', league='Hockeyallsvenskan')
    #scraping.download_all_schedules(league_file, './tmp', regular_season=False)
    games = scraping.get_all_game_numbers('/home/veronica/repos/HockeyStats/tmp/playoff')
    games.sort()
    scraping.download_gamefile(games, src_dir='/home/veronica/hockeystats/Hockeyallsvenskan/2022-23/gamefiles_tmp')
    #store_games(schedules_dir, 4)
    #verify_teamnames(schedules_dir)
    #db_tools.store_players('/home/veronica/hockeystats/Hockeyallsvenskan/2022-23/gamefiles/103364_playsequence-20230312-Hockey Allsvenskan-AISvsAIK-20222023-17101.csv')