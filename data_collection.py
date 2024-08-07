import mysql.connector
import mysql
import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher
import db_tools
import store_players
from sportlogiq import extract_game_info_from_schedules, get_game_numbers_from_schedules
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
        games = extract_game_info_from_schedule_html(file, 2023)
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
        games = extract_game_info_from_schedule_html(file, year=2023)
        print(file,' ', len(games))
        for game in games:
            print('Storing: ', game)
            store_game(game, league_id)

def store_games_from_list(games, league_id):
    for game in games:
        print(game)
        store_game([game['home_team'], game['away_team'], game['date'], game['sl_game_id']], league_id)


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

if __name__ == '__main__':
    import requests
    #for game_id in list(range(137100,137200)):
    #    response = requests.get(f'https://hockey.sportlogiq.com/games/league/{game_id}/video')
    #    print(response)
    #print('apa')
    #t=[1754]
    #scraping.download_all_schedules(sl_team_ids=t, target_dir='./tmp', regular_season=False)
    #exit(0)

    # game_ids = scraping.get_all_game_numbers('/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoff/schedules')

    # game_ids = scraping.get_all_game_numbers('/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoff/schedules')
    # scraping.download_gamefile(game_ids, src_dir='/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoff/gamefiles')

    #exit(0)

    #stats_db = db_tools.open_database()
    #cursor = stats_db.cursor()
    #sql = f"select sl_game_id from game where league_id = 4 and date > \'2023-06-01\';"
    #cursor.execute(sql)
    #games = cursor.fetchall()
    #game_ids = [g[0] for g in games]
    #scraping.download_gamefile(game_ids, src_dir='/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoff/gamefiles')



    # league_file = '/home/veronica/hockeystats/shl-2023-24.txt'
    # league_file = '/home/veronica/hockeystats/NHL/2023-24/regular-season/nhl-2023-24.txt'
    # schedules_dir = '/home/veronica/hockeystats/NHL/2023-24/regular-season/schedules'
    # games_dir = '/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/regular-season/gamefiles'
    # teams = scraping.extract_teams_from_league(league_file)
    # db_tools.store_teams(teams)
    # db_tools.assign_teams(teams, season='2022-23', league='Hockeyallsvenskan')




    #scraping.download_schedules(league_file, './tmp', regular_season=True)
    #games = scraping.get_all_game_numbers('/home/veronica/kk')#hockeystats/NHL/2023-24/regular-season/schedules')

    # verify_scores_schedules_gamefiles()

    # game_numbers = get_game_numbers_from_schedules('/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoffs/schedules')
    #scraping.download_gamefile(game_numbers, src_dir='/home/veronica/hockeystats/NHL/2023-24/playoffs/gamefiles')

    # store_games_from_list(games, 4) #'/home/veronica/hockeystats/NHL/2023-24/regular-season/schedules', 2)

    #verify_teamnames(schedules_dir)
    #root_dir='/home/veronica/hockeystats/Hockeyallsvenskan/2023-24/playoffs/gamefiles'
    #files = os.listdir(root_dir)
    #for file in [os.path.join(root_dir,f) for f in files]:
    #    print(file)
    #    db_tools.store_players(file)
    #ctr = 0
    #for file in [os.path.join(root_dir,f) for f in files]: #[470:]:
    #    print(f"{ctr} of {len(files)} {file}")
    #    db_tools.store_events(file)
    #    ctr += 1

    #game_number = 1
    #entries.line_toi_when_goal(game_number)