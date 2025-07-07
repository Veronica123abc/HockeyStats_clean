#import mysql.connector
#import mysql
#import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher

import pandas as pd
import logging

import apiv2
from sportlogiq import extract_game_info_from_schedules, get_game_numbers_from_schedules
#import sportlogiq
import scraping

import db_tools
import uuid
#import logging
import json
import requests
import browser_cookie3
import api
import re
from datetime import datetime
from dateutil import parser
import db_tools


def get_map():
    map = {
        'period': 'period',
        'period_time': 'period_time',
        'game_time': 'game_time',
        'current_possession': 'possession_id',
        'team_in_possession': 'team_in_possession',
        'current_play_in_possession': 'current_play_in_possession',
        'is_possession_event': 'is_possession_event',
        'is_defensive_event': 'is_defensive_event',
        'is_possession_breaking': 'is_possession_breaking',
        'is_last_play_of_possession': 'is_last_play_of_possession',
        'frame': 'video_frame',
        'timecode': 'timecode',
        'shorthand': 'shorthand',
        'name': 'name',
        'zone': 'zone',
        'type': 'type',
        'outcome': 'outcome',
        'flags': 'flags',
        'previous_name': 'previous_name',
        'previous_type': 'previous_type',
        'previous_outcome': 'previous_outcome',
        'x_coord': 'x_coordinate',
        'y_coord': 'y_coordinate',
        'x_adj_coord': 'x_adjacent_coordinate',
        'y_adj_coord': 'y_adjacent_coordinate',
        'score_differential': 'score_differential',
        'manpower_situation': 'manpower_situation',
        'team_skaters_on_ice': 'team_skaters_on_ice',
        # 'team_forwards_on_ice_refs': 'team_forwards_on_ice_refs',
        # 'team_defencemen_on_ice_refs': 'team_defencemen_on_ice_refs',
        'team_goalie_on_ice_ref': 'team_goalie_id',
        'opposing_team_skaters_on_ice': 'opposing_team_skaters_on_ice',
        # 'opposing_team_forwards_on_ice_refs': 'opposing_team_forwards_on_ice_refs',
        # 'opposing_team_defencemen_on_ice_refs': 'opposing_team_defencemen_on_ice_refs',
        # 'opposing_team_goalie_on_ice_ref': 'opposing_team_goalie_on_ice_ref',
        # 'team': 'team',
        # 'player_jersey': 'player_jersey',
        # 'player_position': 'player_position',
        # 'player_first_name': 'player_first_name',
        # 'player_last_name': 'player_last_name',
        'player_reference_id': 'player_id',
        'players_on_ice': 'players_on_ice',
        'play_zone': 'play_zone',
        'play_section': 'play_section',
        'expected_goals_on_net': 'expected_goals_on_net',
        'expected_goals_all_shots': 'expected_goals_all_shots',
        'expected_goals_on_net_grade': 'expected_goals_on_net_grade',
        'expected_goals_all_shots_grade': 'expected_goals_all_shots_grade'
    }
    inv_map = {map[k]: k for k in map.keys()}
    return map, inv_map



# cursor.execute("SELECT * FROM player WHERE sl_id = %s", (sl_id,))
#         cursor.fetchall()
#         if cursor.rowcount < 1:
#             print('Adding player: ', first_name, ' ', last_name, ' ', team_name, ' ', str(sl_game_id))
#             sql = f"INSERT INTO player (sl_id, firstName, lastName) VALUES ({int(sl_id)}, " \
#                   f"\'{str(first_name)}\', \'{str(last_name)}\');"
#             sql = "INSERT INTO player (sl_id, firstName, lastName) VALUES (%s,%s,%s)"
#             val = (int(sl_id), first_name, last_name)
#             cursor.execute(sql, val)
#             stats_db.commit()
#             added_player +=1
#         cursor.execute(f'select id from player where sl_id={sl_id}')
#         player_id = cursor.fetchall()[0][0]
#         cursor.execute(f'select id from game where sl_game_id = {sl_game_id}')
#         game_id = cursor.fetchall()[0][0]
#
#         sql = f"INSERT INTO affiliation (player_id, game_id, team_id, jersey_number, position) " \
#               f"VALUES ({player_id}, {game_id}, {team_id}, {int(jersey_number)}, \'{position}\');"
#
#
#         try:
#             cursor.execute(sql)
#             stats_db.commit()
#             added_affiliation += 1
#         except:
#             # print('Could not add affiliation. Already stored ...?')
#             not_added_affiliation += 1
#
#     print(added_affiliation, ' ', not_added_affiliation, ' ', added_player)
def longest_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2)
    return match.find_longest_match(0, len(s1),0, len(s2)).size

def get_team_id_from_substring(team_name):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    cursor.execute("select id, name from team")
    all_teams = cursor.fetchall()
    lls = 0
    team_id = -1
    db_team_name = None
    for t in all_teams:
        team=t[1]
        ss = longest_substring(team.lower(), team_name.lower())
        if ss > lls:
             team_id = t[0]
             db_team_name = team
             lls = ss
    return team_id, db_team_name


def create_table_from_sl_json():
    null = None
    record = {

        # "firstName": "vc50",
        # "lastName": "vc50",
        # "displayFirstName": "vc50",
        # "displayLastName": "vc50",
        # "birthdate": "date",
        # "birthCity": "vc50",
        # "birthProvince": "vc50",
        # "birthCountry": "vc50",
        # "nationality": "vc50",
        # "pictureSrc": "vc50",
        # "currentSalary": "int",
        # "freeAgencyStatus": "vc50",
        # "futureFreeAgencyStatus": "vc50",
        # "futureFreeAgencyYear": "int",
        # "injuryStatus": "vc50",
        # "primaryPosition": "vc50",
        # "weight": "int",
        # "height": "int",
        # "laterality": "vc50",
        # "college": "vc50",
        "updatedOn": "datetime"
    }
    type_map = {"vc50": "varchar(255)",
                "int": "int",
                "date": "datetime",
                "datetime": "datetime"}

    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    for key in record.keys():
        column_name = "sl_" + key
        val_type = type_map[record[key]]
        sql = f"alter table player add {column_name} {val_type};"
        cursor.execute(sql)
        stats_db.commit()

def parse_date(date):
    try:
        date = parser.parse(date)
    except:
        return parser.parse('1970-01-01 0:0:0').strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(date,datetime):
        return date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return parser.parse('1970-01-01 0:0:0').strftime('%Y-%m-%d %H:%M:%S')

#def ingest_games(game_data):
def ingest_games(game_data):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()

    data = json.load(open(game_data,"r"))

    cursor.execute("show columns from game;")
    columns = cursor.fetchall()
    column_types = [k[1] for k in columns[12:]]
    column_names = [k[0] for k in columns[12:]] # skip first column (primary key, autoupdated)

    no = len(data['games'])
    ctr = 1
    for game in data['games']:
        cursor.execute(f"select sl_updatedOn from game where sl_id = {game['id']};")
        stored_date = cursor.fetchall()
        if (len(stored_date) > 0):
            stored_date = stored_date[0][0]
        game['created'] = parse_date(game['created'])
        game['updatedOn'] = parse_date(game['updatedOn'])
        game['createdOn'] = parse_date(game['createdOn'])
        game['scheduledTime'] = parse_date(game['scheduledTime'])
        game['scheduledVenueTime'] = parse_date(game['scheduledVenueTime'])
        vals = [game[key] for key in game.keys()]
        vals = [v[0] if v[0] is not None else -1 if v[1]=='int' else '' for v in list(zip(vals, column_types))]
        vals = [-1 if not str(v[0]).isnumeric() and v[1]=='int' else v[0] for v in list(zip(vals, column_types))]
        vals = [1 if str(v[0]) == 'True' and v[1] == 'tinyint(1)' else v[0] for v in list(zip(vals, column_types))]
        vals = [0 if str(v[0]) == 'False' and v[1] == 'tinyint(1)' else v[0] for v in list(zip(vals, column_types))]
        vals = tuple(str(v) for v in vals)
        if stored_date and stored_date < parser.parse(game['updatedOn']):
            print(f"{ctr}: Updating game info ...")
            cursor.execute(f"delete from player where sl_id={game['id']};")
            stats_db.commit()
            sql = f"insert into game ({','.join(column_names)}) values {vals};"
            try:
                cursor.execute(sql)
                stats_db.commit()
            except:
                print(f"Record {ctr}: Failed to execute ", sql)

        elif stored_date:
                print(f"{ctr}: Game already stored with a fresher date ...")
        else:
            sql = f"insert into game ({','.join(column_names)}) values {vals};"
            print(f"Record {ctr}: storing game ... ", sql)
            try:
                cursor.execute(sql)
                stats_db.commit()
            except:
                print(f"Record {ctr}: Failed to execute ", sql)

        ctr += 1


def ingest_players(player_data):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()

    data = json.load(open(player_data,"r"))

    cursor.execute("show columns from player;")
    columns = cursor.fetchall()
    column_types = [k[1] for k in columns[1:]]
    column_names = [k[0] for k in columns[1:]] # skip first column (primary key, autoupdated)

    type_map = {"varchar(255)":"",
                "int": "-1",
                "datetime": parse_date("1970-01-01"),
                }
    no = len(data['players'])
    ctr = 1
    for player in data['players']:
        cursor.execute(f"select sl_updatedOn from player where sl_id = {player['id']};")
        stored_date = cursor.fetchall()
        if (len(stored_date) > 0):
            stored_date = stored_date[0][0]
        player['updatedOn'] = parse_date(player['updatedOn'])
        player['birthdate'] = parse_date(player['birthdate'])
        player['nationality'] = '' if not player['nationality'] else player['nationality']
        vals = [player[key] for key in player.keys()]
        vals.insert(0, player['lastName'])
        vals.insert(0, player['firstName'])
        vals = [v[0] if v[0] is not None else -1 if v[1]=='int' else '' for v in list(zip(vals, column_types))]
        vals = [-1 if not str(v[0]).isnumeric() and v[1]=='int' else v[0] for v in list(zip(vals, column_types))]
        vals = tuple(str(v) for v in vals)
        if stored_date and stored_date < parser.parse(player['updatedOn']):
            print(f"{ctr}: Updating player info ...")
            cursor.execute(f"delete from player where sl_id={player['id']};")
            stats_db.commit()
            sql = f"insert into player ({','.join(column_names)}) values {vals};"
            try:
                cursor.execute(sql)
                stats_db.commit()
            except:
                print(f"Record {ctr}: Failed to execute ", sql)

        elif stored_date:
                print(f"{ctr}: Player already stored with a fresher date ...")
        else:
            sql = f"insert into player ({','.join(column_names)}) values {vals};"
            print(f"Record {ctr}: storing player ... ", sql)
            try:
                cursor.execute(sql)
                stats_db.commit()
            except:
                print(f"Record {ctr}: Failed to execute ", sql)

        ctr += 1

def ingest_teams(team_data):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()

    data = json.load(open(team_data,"r"))
    df =pd.DataFrame.from_dict(data['teams'])
    cursor.execute("show columns from team;")
    column_names = cursor.fetchall()[6:]
    column_names = [k[0] for k in column_names]
    column_names.insert(0,'name')
    #for idx, values in df.iterrows():
    for team in data['teams']:
        vals = [team['displayName'],
                team['id'],
                team['leagueId'],
                team['location'],
                team['name'],
                1 if (team['defaultHomeOZOnRight']) else 0,
                team['shorthand'],
                team['displayName'],
                team['defaultVenueId'],
                -1 if not(team['pastTeamId']) else team['pastTeamId'],
                parse_date(team['createdOn']),
                parse_date(team['updatedOn'])
                ]
        vals = tuple(str(v) for v in vals)
        sql = f"insert into team ({','.join(column_names)}) values {vals};"
        try:
            cursor.execute(sql)
            stats_db.commit()
        except:
            print("Failed to execute ", sql)

def ingest_leagues(league_data):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()


    data = json.load(open(league_data,"r"))
    df =pd.DataFrame.from_dict(data)
    column_names = ["sl_" + str(k) for k in list(data[0].keys())[:-1]]
    column_names = ['name'] + column_names
    for idx, values in df.iterrows():
        vals = list(values)[:-1]
        vals.insert(0,vals[1])
        vals[7] = parse_date(vals[7])
        vals = tuple(str(v) for v in vals)
        #vals[7] = parse_date(vals[7])
        print("storing ", vals[0])
        sql = f"insert into league ({','.join(column_names)}) values {vals};"
        try:
            cursor.execute(sql)
            stats_db.commit()
        except:
            print("Failed to execute ", sql)


def create_clean_dataframe(game):

    team_map = team_ids_from_name(game)
    stats_db = db_tools.open_database(db_name="hockeystats_ver2")
    cursor = stats_db.cursor()
    cursor.execute(f"select id from game where sl_id={game['id']};")
    game_id = cursor.fetchall()[0][0]
    df = pd.DataFrame.from_records(game['events'])
    # add a counter as sl_id and also the game_id to every event
    df['sl_id'] = pd.Series([x for x in range(len(df.index))])
    df['game_id'] = pd.Series([game_id for x in range(len(df.index))])
    # Substitute team-name with team_id
    #teams = df['team_in_possession'].dropna().unique().tolist()
    #teams = [t for t in teams if not t=='None']
    #team_map={}
    #for team in teams:
    #    team_map[team], _ = get_team_id_from_substring(team)
    team_in_possession = df.team_in_possession
    tip = team_in_possession.dropna().apply(lambda t: team_map.get(t))
    df['team_in_possession'] = tip
    team = df.team
    tip = team.dropna().apply(lambda t: team_map.get(t))
    df['team'] = tip
    df['flags'] = df['flags'].apply(lambda x: str(x) if isinstance(x,list) else x)

    apoi = df['team_forwards_on_ice_refs'].dropna() + df['team_defencemen_on_ice_refs'].dropna() + \
           df['team_goalie_on_ice_ref'].dropna().apply(lambda x: [x]) + df['opposing_team_forwards_on_ice_refs'].dropna() + \
           df['opposing_team_defencemen_on_ice_refs']+ df['opposing_team_goalie_on_ice_ref'].dropna().apply(lambda x: [x])
    apoi = apoi.dropna().apply(lambda x:[k for k in x if k.isnumeric()])
    df['all_players_on_ice'] = apoi
    apig = list(set(apoi.sum()))
    cursor.execute(f"select id, sl_id from player where sl_id in {tuple(apig)};")
    all_players = cursor.fetchall()
    player_map = {str(v):str(k) for (k,v) in all_players}
    apoi = apoi.apply(lambda x: [player_map[k] for k in x])
    vals = [t for t in zip(list(apoi.index), list(apoi))]
    vals = [(v[0], p) for v in vals for p in v[1]]
    df['players_on_ice']=apoi

    return df
def team_ids_from_name(game):
    # Extract the stored team_names and ids from database
    sl_game_id = game['id']
    events = game['events']
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    #cursor.execute(f"select sl_homeTeamId, sl_awayTeamId  from game where sl_id={sl_game_id};")
    cursor.execute(f"select home_team_id, away_team_id  from game where sl_id={sl_game_id};")
    team_ids = cursor.fetchall()[0]
    team_ids = [int(t) for t in team_ids]
    cursor.execute(f"select sl_displayName from team where id in {tuple(team_ids)};")
    team_names = [t[0] for t in cursor.fetchall()]

    # Extract teamnames from playsequence
    teams = list(set([k['team_in_possession'] for k in events]))
    teams = [t for t in teams if t]
    teams = [t for t in teams if t != 'None']
    if longest_substring(teams[0], team_names[0]) < longest_substring(teams[0], team_names[1]):
        teams_map =  {team_names[0]:team_ids[0], team_names[1]:team_ids[1]}
    else:
        teams_map = {team_names[0]: team_ids[1], team_names[1]:team_ids[0]}
    return teams_map

def get_player_id(sl_id):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    try:
        cursor.execute(f"select id from player where sl_id={sl_id};")
        id = cursor.fetchall()[0]
    except:
        id = None
    return id

def get_team_id(sl_id):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    try:
        cursor.execute(f"select id from team where sl_id={sl_id};")
        id = cursor.fetchall()[0]
    except:
        id = None
    return id

# def add_shift_times(game_id, source_dir):
#     shifts = create_frame_to_time(game_id, source_dir)

def ingest_affiliation(files):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    game_id = int(os.path.splitext()[0])
    for file in files:
        with open(file,"r") as f:
            roster = json.load(f)
        for team_id in roster.keys():
            team_id = get_team_id(team_id)
            for player in roster[team_id]['players']:
                try:
                    player_id = get_player_id(player)
                    if player_id:
                        cursor.execute(f"insert into affiliation (player_id, game_id, team_id, position) values ({player_id}, {game_id}, {int(team_id)}, {player['position']})")
                        stats_db.commit()
                except:
                    print("could not add affiliation")

def ingest_events(filename):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()

    with open(filename,"r") as f:
        game = json.load(f)

    # team_names_map = team_ids_from_name(game)

    map = {
        'period': 'period',
        'period_time': 'period_time',
        'game_time': 'game_time',
        'current_possession': 'possession_id',
        'team_in_possession': 'team_in_possession',
        'current_play_in_possession': 'current_play_in_possession',
        'is_possession_event': 'is_possession_event',
        'is_defensive_event': 'is_defensive_event',
        'is_possession_breaking': 'is_possession_breaking',
        'is_last_play_of_possession': 'is_last_play_of_possession',
        'frame': 'video_frame',
        'timecode': 'timecode',
        'shorthand': 'shorthand',
        'name': 'name',
        'zone': 'zone',
        'type': 'type',
        'outcome': 'outcome',
        'flags': 'flags',
        'previous_name': 'previous_name',
        'previous_type': 'previous_type',
        'previous_outcome': 'previous_outcome',
        'x_coord': 'x_coordinate',
        'y_coord': 'y_coordinate',
        'x_adj_coord': 'x_adjacent_coordinate',
        'y_adj_coord': 'y_adjacent_coordinate',
        'score_differential': 'score_differential',
        'manpower_situation': 'manpower_situation',
        'team_skaters_on_ice': 'team_skaters_on_ice',
        #'team_forwards_on_ice_refs': 'team_forwards_on_ice_refs',
        #'team_defencemen_on_ice_refs': 'team_defencemen_on_ice_refs',
        'team_goalie_on_ice_ref': 'team_goalie_id',
        'opposing_team_skaters_on_ice': 'opposing_team_skaters_on_ice',
        #'opposing_team_forwards_on_ice_refs': 'opposing_team_forwards_on_ice_refs',
        #'opposing_team_defencemen_on_ice_refs': 'opposing_team_defencemen_on_ice_refs',
        #'opposing_team_goalie_on_ice_ref': 'opposing_team_goalie_on_ice_ref',
        #'team': 'team',
        #'player_jersey': 'player_jersey',
        #'player_position': 'player_position',
        #'player_first_name': 'player_first_name',
        #'player_last_name': 'player_last_name',
        'player_reference_id': 'player_id',
        'players_on_ice': 'players_on_ice',
        'play_zone': 'play_zone',
        'play_section': 'play_section',
        'expected_goals_on_net': 'expected_goals_on_net',
        'expected_goals_all_shots': 'expected_goals_all_shots',
        'expected_goals_on_net_grade': 'expected_goals_on_net_grade',
        'expected_goals_all_shots_grade': 'expected_goals_all_shots_grade'
    }
    #inv_map = {map[k]: k for k in map.keys()}
    sl_game_id = game['id']
    game_id = db_tools.get_game_id(sl_game_id=sl_game_id)
    #columns = list(map.values())
    #events = [{k:event[inv_map[k]] for k in columns} for event in game['events']]
    #sl_id = [{'sl_id': k, 'game_id':game_id} for k in list(range(1,len(events)+1))]
    #[e.update(k) for e,k in zip(events, sl_id)]

    df = create_clean_dataframe(game)
    df.rename(columns=map, inplace=True)
    df.replace('','NULL', inplace=True)
    #df.replace(np.nan,'NULL', inplace=True)
    df.replace(True,1,inplace=True)
    df.replace(False, 0, inplace=True)

    cursor.execute(f"show columns in event;")
    db_columns = cursor.fetchall()
    db_columns = [k[0] for k in db_columns]
    drop_columns = [c for c in df.columns if c not in db_columns]
    df = df.drop(drop_columns, axis=1)
    events = df.to_dict(orient='records')
    ctr = 0
    fail = []
    success = []
    for event in events:
        ctr = ctr+1
        vals = tuple(v for v in event.values())
        vals = f"{tuple(k for k in vals)}".strip()
        vals = re.sub("\'NULL\'", 'NULL', vals)
        #vals = [str(k) for k in vals]
        #vals = ", ".join(vals)
        sql = f"insert into event ({','.join(list(event.keys()))}) values {vals};"

        sql = f"INSERT INTO event ({','.join(list(event.keys()))}) VALUES (" + ', '.join(len(event.values())*['%s']) + ');'
        val = tuple([c for c in event.values()])

        try:
            print(f"{ctr} of {len(events)}")
            cursor.execute(sql)
            stats_db.commit()
            success.append(ctr)
            event_id = cursor.lastrowid
            players_on_ice = [] if event['players_on_ice'] == 'NULL' else event['players_on_ice']
            #players_on_ice = [] if players_on_ice=='NULL' else players_on_ice
            for player in players_on_ice:
                try:
                    cursor.execute(f"insert into player_on_ice (event_id, game_id, player_id) values ({game_id},{event_id},{player});")
                    stats_db.commit()
                except:
                    print(f"failed to store player_on_ice {game_id}, {event_id},{player}")
        except:
            fail.append(ctr)
            print(f"Failed to store {ctr}")
            print(sql)

    print(f"stored {len(success)} of {len(success+fail)}")
    print("end")
    #
    #
    # cursor.execute("show columns from event;")
    # columns = cursor.fetchall()
    # column_types = [k[1] for k in columns[1:]]
    # column_names = [k[0] for k in columns[1:]]
    #
    # ctr=0
    # for event in events:
    #     ctr=ctr+1
    #     print(ctr)
    #     for n,t in zip(column_names, column_types):
    #         if t=='float':
    #             event[n] = 'NULL' if not event[n] else float(event[n])
    #     mapping = {None: 'NULL', 'None': 'NULL', True: 1, False: 0}
    #     mapping.update(teams_map)
    #     for key in event.keys():
    #         if isinstance(event[key], list):
    #             event[key] = ", ".join(event[key])
    #         else:
    #             event[key] = mapping.get(event[key], event[key])
    #
    #
    #
    #
    #     vals = tuple(v for v in event.values())
    #     vals = f"{tuple(k for k in vals)}"
    #     vals = re.sub("\'NULL\'", 'NULL', vals)
    #     #vals = [str(k) for k in vals]
    #     #vals = ", ".join(vals)
    #     sql = f"insert into event ({','.join(list(event.keys()))}) values {vals};"
    #
    #     #print(sql)
    #     try:
    #         cursor.execute(sql)
    #         stats_db.commit()
    #     except:
    #         print("Failed to execute ", sql)
    #
    # sl_game_id = int(os.path.basename(gamefile).split('_')[0])
    # df = pd.read_csv(gamefile)
    # game_id = get_game_id(sl_game_id=str(sl_game_id))
    # game_id_column = df.gameReferenceId.apply(lambda x: game_id)
    # df.gameReferenceId = game_id_column
    # df = clean_dataframe(df)
    # df = df.rename(columns=inv_map)
    # df = df[list(map.keys())]
    # players_on_ice = df[['sl_id', 'players_on_ice']]
    # df.drop('players_on_ice', inplace=True, axis=1)
    # entries = df.to_dict(orient='records')

    for e in entries:
        new_record=[(k, e[k]) for k in e.keys() if pd.notna(e[k])]
        columns = ', '.join([c[0] for c in new_record])
        sql = "INSERT INTO event (" + columns + ") VALUES (" + ', '.join(len(new_record)*['%s']) + ');'
        val = tuple([c[1] for c in new_record])
        event_id = e['sl_id']
        logging.debug(f"======== Trying to register event {event_id} in game {game_id}========================\n")
        try:
            logging.debug(new_record)
            logging.debug('\n')
            cursor.execute(sql, val)
            logging.debug('mysql registered event successfully \n')
        except:
            print(str(event_id), 'Could not register event. Already registered ...?')
            logging.debug('mysql failed to register event')

    logging.debug('Trying to commit events to database')
    try:
        stats_db.commit()
        logging.debug('mysql committed successfully')
    except:
        print('Could not commit')
        logging.debug(f"mysql failed to commit changes for game {game_id}")

    print("Storing players on ice for each event\n")
    entries = players_on_ice.to_dict(orient='records')
    for e in entries:
        cursor.execute(f"SELECT id from event where sl_id={e['sl_id']} and game_id={game_id};")
        event_id = cursor.fetchall()[0][0]
        # store_players_on_ice(event_id, e['players_on_ice'], cursor)
        players=e['players_on_ice']
        for player in players:
            sql = "INSERT INTO player_on_ice (player_id, event_id) VALUES (%s, %s);"
            val = (player, event_id)
            try:
                cursor.execute(sql, val)
            except:
                pass
                #print("Could not add player with id " + str(player) + " to be on ice during event " + str(event_id))

    logging.debug('Trying to commit to database')
    try:
        stats_db.commit()
        logging.debug('mysql committed successfully')
    except:
        print('Could not commit')
        logging.debug(f"mysql failed to commit changes for game {game_id}")

def create_game_table():
    record = {
        "id": "int",
        "leagueId": "int",
        "awayTeamId": "int",
        "homeTeamId": "617",
        "ownerCompanyId": "vc(255",
        "seasonId": "int",
        "seasonStage": "vc(255)",
        "created": "2018-09-12 17:00:17.333323+00",
        "comment": "",
        "venueId": "245",
        "scheduledTime": "2019-03-05T17:00:00+00:00",
        "scheduledVenueTime": "2019-03-05T12:00:00-05:00",
        "gameLength": null,
        "attendance": null,
        "createdOn": "1970-01-01 00:00:00+00",
        "updatedOn": "2025-01-18 07:37:38.800872+00",
        "isPostponed": False,
        "periodCount": 3,
        "referenceId": "8566"
    }

    type_map = {"vc50": "varchar(255)",
                "int": "int",
                "date": "datetime",
                "datetime": "datetime"}

    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    for key in record.keys():
        column_name = "sl_" + key
        val_type = type_map[record[key]]
        sql = f"alter table player add {column_name} {val_type};"
        cursor.execute(sql)
        stats_db.commit()

def create_player_table():
    record = {

        "firstName": "vc50",
        "lastName": "vc50",
        "displayFirstName": "vc50",
        "displayLastName": "vc50",
        "birthdate": "date",
        "birthCity": "vc50",
        "birthProvince": "vc50",
        "birthCountry": "vc50",
        "nationality": "vc50",
        "pictureSrc": "vc50",
        "currentSalary": "int",
        "freeAgencyStatus": "vc50",
        "futureFreeAgencyStatus": "vc50",
        "futureFreeAgencyYear": "int",
        "injuryStatus": "vc50",
        "primaryPosition": "vc50",
        "weight": "int",
        "height": "int",
        "laterality": "vc50",
        "college": "vc50",
        "updatedOn": "datetime"
    }
    type_map = {"vc50": "varchar(255)",
                "int": "int",
                "date": "datetime",
                "datetime": "datetime"}

    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    for key in record.keys():
        column_name = "sl_" + key
        val_type = type_map[record[key]]
        sql = f"alter table player add {column_name} {val_type};"
        cursor.execute(sql)
        stats_db.commit()

def add_scores(data):
    scores = json.load(open(data,"r"))['scores']
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    for game in list(scores.keys()):
        item = scores['game']
        score = item['score']
        if score is not None:
            #home_team_id = item[]
            sql = f"update game set home_team_goals={item['score']}"
    #.execut

if __name__ == '__main__':
    #apiv2.download_games(137670)

    ingest_events("/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/137556.json")
    add_scores("/home/veronica/hockeystats/ver2/SHL/all_games_13.json")
    #ingest_games("/home/veronica/hockeystats/ver2/SHL/all_games_13.json")
    #ingest_teams("/home/veronica/hockeystats/ver2/all_teams.json")
    base_path = ("/home/veronica/hockeystats/ver2")
    dirs = os.listdir(base_path)
    ctr = 1
    total = len(dirs)
    for dir in [d for d in dirs if os.path.isdir(os.path.join(base_path,d))]:
        print(f"{dir} ({ctr} of {total})")
        # if os.path.splitext(dir)[1] in ['.json', 'json']:
        #     print("kjk")
        files = os.listdir(f"/home/veronica/hockeystats/ver2/{dir}")
        games = [f for f in files if 'games' in f][0]
        ctr = ctr+1
        #ingest_players("/home/veronica/hockeystats/ver2/Beijer_Hockey_Games/all_players_314.json")
        ingest_games(os.path.join(base_path, dir, games))
    null = None

