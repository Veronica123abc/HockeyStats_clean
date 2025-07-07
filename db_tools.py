import mysql.connector
import mysql
import pandas as pd
import numpy as  np
import os
import uuid

#from generate_entry_statistics import stats_db
from sportlogiq import extract_game_info_from_schedules
from difflib import SequenceMatcher
import logging
import re
import json

APOI = None

map = {'id':'id','game_id': 'gameReferenceId', 'expected_goals_all_shots': 'expectedGoalsAllShots',
       'expected_goals_on_net': 'expectedGoalsOnNet',
       'flags': 'flags', 'game_time': 'gameTime', 'sl_id': 'id', 'is_defensive_event': 'isDefensiveEvent',
       'is_last_play_of_possession': 'isLastPlayOfPossession', 'is_possession_breaking': 'isPossessionBreaking',
       'is_possession_event': 'isPossessionEvent', 'manpower_situation': 'manpowerSituation', 'name': 'name',
       'outcome': 'outcome', 'period': 'period', 'period_time': 'periodTime',
       'play_in_possession': 'currentPlayInPossession',
       'play_zone': 'playZone', 'possession_id': 'currentPossession', 'previous_name': 'previousName',
       'previous_outcome': 'previousOutcome', 'previous_type': 'previousType', 'player_id': 'playerReferenceId',
       'team_goalie_id': 'teamGoalieOnIceRef', 'opposing_team_goalie_id': 'opposingTeamGoalieOnIceRef',
       'score_differential': 'scoreDifferential', 'shorthand': 'shorthand',
       'team_in_possession': 'teamInPossession', 'team_skaters_on_ice': 'teamSkatersOnIce', 'timecode': 'timecode',
       'video_frame': 'frame', 'x_adjacent_coordinate': 'xAdjCoord', 'x_coordinate': 'xCoord',
       'y_adjacent_coordinate': 'yAdjCoord', 'y_coordinate': 'yCoord', 'zone': 'zone', 'type': 'type',
       'players_on_ice': 'apoi', 'player_on_ice':'apoi', 'team_id': 'team'}

def get_map():

    inv_map = {map[k] : k for k in map.keys()}
    return map, inv_map

def convert_to_string(n):
    if pd.isna(n):
        return ''
    elif isinstance(n, int):
        return(str(n))
    elif isinstance(n, float):
        return(str(int(n)))
    else:
        numbers = re.findall('\d+', n)
        res = ' '
        for n in numbers:
            res = res + ' ' + n + ' '
        return res

def open_database(db_name="hockeystats_ver2"):
    stats_db = mysql.connector.connect(
        host="localhost",
        user="apa",
        auth_plugin='mysql_native_password',
        password="apa",
        database=db_name,
    )
    return stats_db

def player_on_ice(df, player_id):
    global APOI
    all_players_on_ice = (df.teamForwardsOnIceRefs.apply(convert_to_string) + \
                           df.teamDefencemenOnIceRefs.apply(convert_to_string) + \
                           df.teamGoalieOnIceRef.apply(convert_to_string) + \
                           df.opposingTeamForwardsOnIceRefs.apply(convert_to_string) + \
                           df.opposingTeamDefencemenOnIceRefs.apply(convert_to_string) + \
                           df.opposingTeamGoalieOnIceRef.apply(convert_to_string)).dropna()

    df = df.loc[all_players_on_ice.index]
    if APOI is None:
        APOI = [re.sub("[^0-9]", " ", s) for s in all_players_on_ice]
    return df[[player_id in on_ice for on_ice in APOI]]

def add_all_players_on_ice(df):
    apoi = all_players_on_ice(df)
    df['apoi'] = APOI  # all_players_on_ice
    return df

def all_players_in_game(df):
    apoi = all_players_on_ice(df)
    apig = list(set([int(float(s)) for s in ''.join(apoi).split(' ') if len(s) > 0]))

    return apig

def add_all_players_on_ice(df):
    apoi = all_players_on_ice(df)
    df['apoi'] = APOI  # all_players_on_ice
    return df
def all_players_on_ice(df):
    all_players_on_ice = (df.teamForwardsOnIceRefs.apply(convert_to_string) + \
                           df.teamDefencemenOnIceRefs.apply(convert_to_string) + \
                           df.teamGoalieOnIceRef.apply(convert_to_string) + \
                           df.opposingTeamForwardsOnIceRefs.apply(convert_to_string) + \
                           df.opposingTeamDefencemenOnIceRefs.apply(convert_to_string) + \
                           df.opposingTeamGoalieOnIceRef.apply(convert_to_string)).dropna()
    apoi = [re.sub("[^0-9]", " ", s) for s in all_players_on_ice]
    return apoi

def all_players_on_ice_as_int(apoi, map):
    res=[]
    for item in apoi:
        ids = []
        sl_ids = list(set([int(float(s)) for s in ''.join(item).split(' ') if len(s) > 0]))
        for sl_id in sl_ids:
            try:
                ids.append(map[sl_id])
            except:
                print(f'Player with sl_id {sl_id} is not registered in the database')
        res.append(ids)
    return res

def get_player_id(player, map):
    numbers = re.findall('\d+', player)
    if len(numbers) > 0:
    #if len(player) > 0:
        return map.get(int(float(player)))
    else:
        return None

def add_player_and_goalies(df, map):
    player = df.playerReferenceId.apply(convert_to_string)
    player = player.apply(get_player_id, map=map)
    goalie = df.teamGoalieOnIceRef.apply(convert_to_string)
    goalie = goalie.apply(get_player_id, map=map)
    opposing_goalie = df.opposingTeamGoalieOnIceRef.apply(convert_to_string)
    opposing_goalie = opposing_goalie.apply(get_player_id, map=map)
    #goalie = df.teamGoalieOnIceRef.apply(convert_to_string)
    #opposingGoalie = df.opposingTeamGoalieOnIceRef.apply(convert_to_string)
    df['playerReferenceId'] = player
    df['teamGoalieOnIceRef'] = goalie
    df['opposingTeamGoalieOnIceRef'] = opposing_goalie
    return df

def clean_dataframe(df):

    stats_db = open_database()
    cursor = stats_db.cursor()

    # Substitute team-name with team_id
    teams = df['teamInPossession'].dropna().unique().tolist()
    teams = [t for t in teams if not t=='None']
    team_map={}
    for team in teams:
        team_map[team], _ = get_team_id_from_substring(team)
    team_in_possession = df.teamInPossession
    tip = team_in_possession.dropna().apply(lambda t: team_map.get(t))
    df['teamInPossession'] = tip

    apig = all_players_in_game(df)
    player_map={}
    for player in apig:
        try:
            cursor.execute(f'select id from player where sl_id={player}')
            player_id=cursor.fetchall()[0][0]
            player_map[player] = player_id
        except:
            print(f'Player with sportlogic reference id {player} is not stored in the database')

    apoi = all_players_on_ice(df)
    apoi_int = all_players_on_ice_as_int(apoi, player_map)
    df['apoi'] = pd.Series(apoi_int)
    df = add_player_and_goalies(df, player_map)
    return df

def longest_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2)
    return match.find_longest_match(0, len(s1),0, len(s2)).size

def find_new_teams(teams):
    new_teams = []
    for team in teams:
        team_id, team_name = get_team_from_sl_id(team['sl_id'])
        if team_id is None:
            new_teams.append(team)
    return new_teams

def create_teamname_map(items):
    if isinstance(items[0], str):
        items = [{'sl_name' : teamname, 'sl_id': -1} for teamname in items]
    map = []
    for item in items:
        id, name = get_team_from_sl_id(item['sl_id'])
        if id is None:
            id, name = get_team_id_from_substring(item['sl_name'])
        item['id'] = id
        item['name'] = name
        map.append(item)
    res = []
    with open("map.json", "w") as f:
        json.dump(map, f, indent=4)
    return map

def load_teams_from_file(map_filename):
    with open(map_filename) as f:
        map = json.load(f)
    return map

def get_team_from_sl_id(sl_id):
    stats_db = open_database()
    cursor = stats_db.cursor()
    sql = f"select distinct team.id, team.name from team join participation on team.id = participation.team_id where participation.sl_team_id={sl_id};"
    cursor.execute(sql)
    existing_team_ids = cursor.fetchall()
    if len(existing_team_ids) >0:
        return int(existing_team_ids[0][0]), existing_team_ids[0][1]
    else:
        return None, None

def get_team_id_from_substring(team_name):
    stats_db = open_database()
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

def store_players(filename):
    nan=np.nan
    added_affiliation = 0
    added_player = 0
    not_added_affiliation = 0
    stats_db = open_database()
    df = pd.read_csv(filename)
    skaters = df.query("playerReferenceId not in [@nan, 'None']").playerReferenceId.unique()
    sl_game_id = int(os.path.basename(filename).split('_')[0])
    for skater in skaters:
        skater_data = df.query("playerReferenceId == @skater")
        team_name = skater_data.team.unique()[0]
        team_id, _ = get_team_id_from_substring(team_name)
        first_name = skater_data.playerFirstName.unique()[0]
        last_name = skater_data.playerLastName.unique()[0]
        jersey_number = skater_data.playerJersey.unique()[0]
        position = skater_data.playerPosition.unique()[0]
        cursor = stats_db.cursor()
        sl_id=int(skater)
        cursor.execute("SELECT * FROM player WHERE sl_id = %s", (sl_id,))
        cursor.fetchall()
        if cursor.rowcount < 1:
            print('Adding player: ', first_name, ' ', last_name, ' ', team_name, ' ', str(sl_game_id))
            sql = f"INSERT INTO player (sl_id, firstName, lastName) VALUES ({int(sl_id)}, " \
                  f"\'{str(first_name)}\', \'{str(last_name)}\');"
            sql = "INSERT INTO player (sl_id, firstName, lastName) VALUES (%s,%s,%s)"
            val = (int(sl_id), first_name, last_name)
            cursor.execute(sql, val)
            stats_db.commit()
            added_player +=1
        cursor.execute(f'select id from player where sl_id={sl_id}')
        player_id = cursor.fetchall()[0][0]
        cursor.execute(f'select id from game where sl_game_id = {sl_game_id}')
        game_id = cursor.fetchall()[0][0]

        sql = f"INSERT INTO affiliation (player_id, game_id, team_id, jersey_number, position) " \
              f"VALUES ({player_id}, {game_id}, {team_id}, {int(jersey_number)}, \'{position}\');"


        try:
            cursor.execute(sql)
            stats_db.commit()
            added_affiliation += 1
        except:
            # print('Could not add affiliation. Already stored ...?')
            not_added_affiliation += 1

    print(added_affiliation, ' ', not_added_affiliation, ' ', added_player)
def store_players_old(filename):
    stats_db = open_database()
    nan = np.nan
    df = pd.read_csv(filename)
    skaters = df.query("playerReferenceId not in [@nan, 'None']").playerReferenceId.unique()
    goalies = df.query("teamGoalieOnIceRef not in [@nan, 'None']").teamGoalieOnIceRef.unique()

    for skater in skaters:
        skater_data = df[df.playerReferenceId == skater]
        cursor = stats_db.cursor()
        sl_id=int(skater)
        cursor.execute("SELECT * FROM player WHERE sl_id = %s", (sl_id,))
        cursor.fetchall()
        # print(cursor.rowcount)
        if cursor.rowcount < 1:
            print('Adding player ', skater_data.playerFirstName.iloc[0], ' ', skater_data.playerLastName.iloc[0])
            sql = "INSERT INTO player (sl_id, firstName, lastName ) VALUES (%s, %s, %s)"
            val = (int(skater_data.playerReferenceId.iloc[0]), skater_data.playerFirstName.iloc[0], skater_data.playerLastName.iloc[0])
            cursor.execute(sql, val)
            stats_db.commit()


        #cursor.execute("SELECT SL_key from player"):


def store_team():
    stats_db = open_database()
    cursor = stats_db.cursor()
    team = ['Leksand','','LIF',324]
    sql = "INSERT INTO team (name, suffix, sl_code, sl_id) VALUES (%s, %s, %s, %s)"
    val = (team[0], team[1], team[2], 310)
    cursor.execute(sql, val)
    stats_db.commit()

def store_teams(teams):
    stats_db = open_database()
    cursor = stats_db.cursor()
    #sql = "SELECT sl_id from team"
    sql = "select distinct participation.sl_team_id, team.id, team.name from team join participation on team.id = participation.team_id;"
    cursor.execute(sql)
    existing_team_ids = cursor.fetchall()
    existing_team_ids = [e[0] for e in existing_team_ids]
    new_teams = [t for t in teams if t['sl_id'] not in existing_team_ids]
    for team in new_teams:
        if team['id']>0: #team does not exist
            sql = f"INSERT INTO team (name, sl_name) VALUES ('{team['name']}', '{team['sl_name']}');"
            try:
                cursor.execute(sql)
            except:
                print("Error in query: ", sql)
    stats_db.commit()

def assign_teams(teams, season, league):
    stats_db = open_database()
    cursor = stats_db.cursor()
    if isinstance(league, str):
        cursor.execute(f"SELECT id from league where name='{league}'")
        league_id = cursor.fetchall()[0][0]
    else:
        league_id = league
    for team in teams:
        sql = f"INSERT INTO participation (league_id, team_id, sl_team_id, season) "\
              f"VALUES ({league_id}, {team['id']}, {team['sl_id']}, '{season}')"
        try:
            cursor.execute(sql)
        except:
            print("Error in query: ", sql)
    stats_db.commit()

def get_plain_name(team_name):
    stats_db = open_database()
    cursor = stats_db.cursor()
    cursor.execute("select name from team")
    all_teams = cursor.fetchall()
    for team in [t[0] for t in all_teams]:
        if len(team_name.split(team)) > 1:
            return team
    return None

def get_all_teams():
    '''
    :return:Get the entire database table team
    '''
    stats_db = open_database()
    cursor = stats_db.cursor()
    cursor.execute("select * from team")
    return cursor.fetchall()

def get_team(sl_id):
    '''
    Get database id and database name for the team with sportlogiq-id sl_id
    :param sl_id: teams id in sportlogiq
    :return: teams' id in database and name in database
    '''
    stats_db = open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    cursor.execute(f"select id, name from team where sl_id={sl_id};")
    res = cursor.fetchall()[0]
    return res

def get_teams(game_id):
    '''
    :param game_id: sportlogiq id of th game
    :return: sportlogiq id for hometeam and awayteam
    '''
    stats_db = open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    sql = f"select sl_homeTeamId, sl_awayTeamId from game where sl_id={game_id};"
    cursor.execute(sql)
    return cursor.fetchall()[0]

# def get_team_id(team_name):
#     stats_db = open_database()
#     cursor = stats_db.cursor()
#     name = get_plain_name(team_name)
#     sql = "select id from team where name=%s"
#     values = (name,)
#     cursor.execute(sql, values)
#     id = cursor.fetchall()
#     if len(id) > 0:
#         return id[0][0]
#     else:
#         return -1

def get_team_name(team_id):
    stats_db = open_database()
    cursor = stats_db.cursor()
    sql = f"select name from team where id={team_id};"
    cursor.execute(sql)
    teams = cursor.fetchall()
    if len(teams) == 1:
        return teams[0][0]
    else:
        print("Team with id ", team_id, " is not stored in the database.")
        return str(team_id)

def get_game_id(sl_game_id = None, sl_game_reference_id = None):
    stats_db = open_database()
    cursor = stats_db.cursor()
    if sl_game_id:
        query = f"select id from game where sl_id = {sl_game_id};"
    elif sl_game_reference_id:
        query = f"select id from game where sl_game_reference_id = {sl_game_reference_id};"
    else:
        return -1
    cursor.execute(query)
    game_id = cursor.fetchall()[0][0]
    return game_id


# def add_sl_team_id(teams):
#     stats_db = open_database()
#     cursor = stats_db.cursor()
#     for team in teams:
#         sql = f"UPDATE team set sl_id={team['sl_id']} where id={team['id']};"
#         try:
#             cursor.execute(sql)
#         except:
#             print("SQL error when inserting")
#     stats_db.commit()
#     print("apa")



def store_events(gamefile):

    #log_root = '/home/veronica/hockeystats/logs'
    #event_log = os.path.join(log_root, 'events')
    #log_file = os.path.basename(gamefile).split('_')[0] + '_' + str(uuid.uuid4()) + '.log'
    #logging.basicConfig(filename=os.path.join(event_log, log_file), level=logging.DEBUG, format='')
    #logger = logging.getLogger('event_logger')
    #logger.setLevel(logging.DEBUG)


    #print("Begin storing events. Logging to " + os.path.join(event_log, log_file))
    logging.debug('Storing events from ' + gamefile + '\n')

    stats_db = open_database()
    cursor = stats_db.cursor()

    map = {'game_id':'gameReferenceId', 'expected_goals_all_shots': 'expectedGoalsAllShots', 'expected_goals_on_net': 'expectedGoalsOnNet',
     'flags': 'flags', 'game_time': 'gameTime', 'sl_id': 'id', 'is_defensive_event': 'isDefensiveEvent',
     'is_last_play_of_possession': 'isLastPlayOfPossession', 'is_possession_breaking': 'isPossessionBreaking',
     'is_possession_event': 'isPossessionEvent', 'manpower_situation': 'manpowerSituation', 'name': 'name',
     'outcome': 'outcome', 'period': 'period', 'period_time': 'periodTime', 'play_in_possession': 'currentPlayInPossession',
     'play_zone': 'playZone', 'possession_id': 'currentPossession', 'previous_name': 'previousName',
     'previous_outcome': 'previousOutcome', 'previous_type': 'previousType', 'player_id':'playerReferenceId',
     'team_goalie_id':'teamGoalieOnIceRef', 'opposing_team_goalie_id': 'opposingTeamGoalieOnIceRef',
     'score_differential': 'scoreDifferential', 'shorthand': 'shorthand',
     'team_in_possession': 'teamInPossession', 'team_skaters_on_ice': 'teamSkatersOnIce', 'timecode': 'timecode',
     'video_frame': 'frame', 'x_adjacent_coordinate': 'xAdjCoord', 'x_coordinate': 'xCoord',
     'y_adjacent_coordinate': 'yAdjCoord', 'y_coordinate': 'yCoord', 'zone': 'zone', 'type': 'type', 'players_on_ice': 'apoi'}

    inv_map = {map[k] : k for k in map.keys()}
    sl_game_id = int(os.path.basename(gamefile).split('_')[0])
    df = pd.read_csv(gamefile)
    game_id = get_game_id(sl_game_id=str(sl_game_id))
    game_id_column = df.gameReferenceId.apply(lambda x: game_id)
    df.gameReferenceId = game_id_column
    df = clean_dataframe(df)
    df = df.rename(columns=inv_map)
    df = df[list(map.keys())]
    players_on_ice = df[['sl_id', 'players_on_ice']]
    df.drop('players_on_ice', inplace=True, axis=1)
    entries = df.to_dict(orient='records')

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

def find_missing_gamefiles(root_dir, league_id=1):
    stat_db = open_database()
    cursor = stat_db.cursor()
    files = os.listdir(root_dir)
    games_files = [int(f.split('_')[0]) for f in files]
    games_files.sort()
    cursor.execute(f'select sl_game_id from game where league_id={league_id} order by sl_game_id')
    games_db = cursor.fetchall()
    games_db = [g[0] for g in games_db]
    missing_games = [g for g in games_db if g not in games_files]
    return missing_games

def extract_teams_from_gamefile(gamefile):
    split_vs = gamefile.split('vs')
    sl_game_id = gamefile.split('_')[0]
    home_team = split_vs[0].split('-')[-1]
    away_team = split_vs[1].split('-')[0]
    return int(sl_game_id), home_team, away_team

def verify_game_files(dir, league_id=1):
    stat_db = open_database()
    cursor = stat_db.cursor()
    files = os.listdir(dir)
    query = ("select game.sl_game_id, team.sl_code, team_2.sl_code, game.date "
             "from game join team join team as team_2 "
             "on game.home_team_id = team.id and game.away_team_id = team_2.id "
             f"where league_id={league_id} order by game.sl_game_id;"
             )
    cursor.execute(query)
    db_games = cursor.fetchall()
    error_messages = []
    error_game_ids = []
    error_game_files = []
    for file in [f for f in files if os.path.splitext(f)[1] == '.csv']:
        sl_game_id, home_team, away_team = extract_teams_from_gamefile(file)
        db_game_teams = [(game[1], game[2]) for game in db_games if game[0] == sl_game_id][0]
        if db_game_teams[0] == away_team and db_game_teams[1] == home_team:
            print('Correct: ', sl_game_id, ' was played by ', db_game_teams[0], ' and ', db_game_teams[1])
        else:
            error_messages.append('Error: ' + str(sl_game_id) + ' was played by ' + db_game_teams[0] + ' and ' + db_game_teams[1])
            error_game_ids.append(sl_game_id)
            error_game_files.append(os.path.join(dir, file))
    return(error_messages, error_game_ids, error_game_files)


def goals_in_season(team_id, league, season, manpower_situation=None):
    stat_db = open_database()
    cursor = stat_db.cursor()
    sql = f"select id from game where home_team_id={team_id} or away_team_id={team_id};"
    cursor.execute(sql)
    games = cursor.fetchall()
    games = [g[0] for g in games]
    res = None
    for game in games:
        goals = goals_in_game(game, manpower_situation=manpower_situation)
        if not res:
            res = goals[team_id]
        else:
            res['goals_ft'] += goals[team_id]['goals_ft']
            res['goals_ot'] += goals[team_id]['goals_ot']
            res['goals_shootout'] += goals[team_id]['goals_shootout']
            res['total'] += goals[team_id]['total']
    return res
def goals_in_game(game_id, team_id=None, manpower_situation=None):
    stat_db = open_database()
    cursor = stat_db.cursor()
    htgf = 0
    atgf = 0
    htgo = 0
    atgo = 0
    htgso = 0
    atgso = 0
    htshootout = 0
    atshootout = 0

    sql = f"select home_team_id, away_team_id from game where id={game_id};"
    cursor.execute(sql)
    teams = cursor.fetchall()
    home_team_id = teams[0][0]
    away_team_id = teams[0][1]

    sql = f"select * from event where game_id={game_id};"
    cursor.execute(sql)
    events = cursor.fetchall()
    cursor.execute("show columns from event;")
    a=cursor.fetchall()
    column_names = [map[c[0]] for c in a]
    df = pd.DataFrame(events, columns=column_names)
    home_team_goals = df.query(
        "name == 'goal' and outcome in ['successful'] and teamInPossession == @home_team_id")
    away_team_goals = df.query(
        "name == 'goal' and outcome in ['successful'] and teamInPossession == @away_team_id")

    df['gameTime'] = df['gameTime'].round()
    if manpower_situation:
        home_team_goals = home_team_goals.query("manpowerSituation == @manpower_situation")
        away_team_goals = away_team_goals.query("manpowerSituation == @manpower_situation")


    home_team_goals_ft = home_team_goals.query("gameTime < 3600")
    away_team_goals_ft = away_team_goals.query("gameTime < 3600")
    home_team_goals_ot = home_team_goals.query("gameTime > 3600") # and gameTime < 3900")
    away_team_goals_ot = away_team_goals.query("gameTime > 3600") # and gameTime < 3900")
    home_team_goals_shootout = df.query("name == 'sogoal' and gameTime == 3900 and teamInPossession == @home_team_id")
    away_team_goals_shootout = df.query("name == 'sogoal' and gameTime == 3900 and teamInPossession == @away_team_id")

    htgso = home_team_goals_shootout.shape[0]
    atgso = away_team_goals_shootout.shape[0]
    htshootout = 1 if htgso > atgso else 0
    atshootout = 1 if atgso > htgso else 0

    htgf = home_team_goals_ft.shape[0]
    atgf = away_team_goals_ft.shape[0]
    htgo = home_team_goals_ot.shape[0]
    atgo = away_team_goals_ot.shape[0]
    htgso = htgso
    atgso = atgso
    htshootout = htshootout
    atshootout = atshootout


    home_team = {'goals_ft': htgf,
                 'goals_ot': htgo,
                 'goals_shootout': htgso,
                 'total': htgf+htgo+htshootout}
    away_team = {'goals_ft': atgf,
                 'goals_ot': atgo,
                 'goals_shootout': atgso,
                 'total': atgf+atgo+atshootout}
    res = {home_team_id: home_team, away_team_id:away_team}
    return res

def get_events_from_game_with_team(game_id, gamefile_names=False):
    stats_db = open_database()
    cursor = stats_db.cursor()
    sql = f"select event.*, affiliation.team_id as team from event left join affiliation on event.player_id=affiliation.player_id and event.game_id=affiliation.game_id where event.game_id={game_id};"
    #sql=f"select * from event where game_id={game_id};"
    cursor.execute(sql)
    events=cursor.fetchall()
    cursor.execute("show columns from event;")
    event_cols = cursor.fetchall()
    cursor.execute("show columns from affiliation where Field='team_id'")
    team_col = cursor.fetchall()
    a = event_cols + team_col
    #a=cursor.fetchall()



    if gamefile_names:
        column_names=[map[c[0]] for c in a]
    else:
        column_names = [c[0] for c in a]
    df = pd.DataFrame(events, columns=column_names)
    return df

def get_events_from_game(game_id, gamefile_names=False):
    stats_db = open_database()
    cursor = stats_db.cursor()
    sql=f"select * from event where game_id={game_id};"
    cursor.execute(sql)
    events=cursor.fetchall()
    cursor.execute("show columns from event;")
    a=cursor.fetchall()

    if gamefile_names:
        column_names=[map[c[0]] for c in a]
    else:
        column_names = [c[0] for c in a]
    df = pd.DataFrame(events, columns=column_names)
    return df

def extract_teams(events):
    nan = np.nan
    teams = events.query("team_in_possession not in [@nan, 'None']").team_in_possession.unique()
    teams = [int(t) for t in teams.tolist()]
    return teams

def teams_in_game(game_id):
    stats_db = open_database()
    cursor = stats_db.cursor()
    sql=f"select home_team_id, away_team_id from game where id={game_id};"
    cursor.execute(sql)
    game_info = cursor.fetchall()
    res = {
            'home_team_id': game_info[0][0],
            'away_team_id': game_info[0][1]
           }
    return res

def run_select_query(sql):
    stats_db = open_database()
    cursor = stats_db.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()

    return res


def verify_events(game_id):
    # sql = f"select * from event where game_id={game_id}"
    events_db = get_events_from_game(game_id, gamefile_names=True)
    print(events_db)

