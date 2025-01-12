import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import colors
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
APOI = None
#from scipy.ndimage import interpolation
import math
import time
import copy



def clean(df,col):
    nan = np.nan
    clean = df[col].dropna()
    return df.loc[clean.index]


def play_sequences(df):
    nan = np.nan
    #df = clean(df, 'name')
    whistles = list(df.loc[df['name'] == 'whistle'].index)
    whistles.insert(0,0) # game begins without a whistle
    seq = list(zip(whistles[:-1], whistles[1:]))
    seq = [{'start_index': s[0], 'end_index': s[1]} for s in seq]
    return seq



def puck_zone(df, team_id=None):
    nan = np.nan
    # if team_id is None:
    teams = df.query("team_in_possession not in [@nan, 'None']").team_in_possession.unique()

    # Use faceoffs to assess which team is hometeam
    home_team_faceoffs = df.query("shorthand=='Face-Off' and type=='hoz'")
    faceoffs = df.query("shorthand == 'Face-Off'")
    team, play_zone = df.iloc[home_team_faceoffs.index[4]+1][['team_id','play_zone']]
    if play_zone == 'oz':
        home_team = team
        away_team = [t for t in list(teams) if t != home_team][0]
    else:
        away_team = team
        home_team = [t for t in list(teams) if t != away_team]

    if team_id is not None:
        team_1 = team_id # teams[0]
        team_2 = [t for t in list(teams) if t != team_id][0]
    else:
        team_1 = home_team
        team_2 = away_team
    df = df.query("is_defensive_event == 0")
    df = df.query("is_possession_event == 1")
    df = df.query("manpower_situation == 'evenStrength'")


    # In sportlogiq, a carry into oz is labeled zone=oz and play_zone=oz. A carry out of dz is labeled
    # Other events that moves across zones are (as I understand) labeled
    # zone=[initial zone] and play_zone=[zone to which the puck moved]. This includes carries out of dz. This means that
    # all zone transitioning events EXCEPT A CARRY INTO OZ follows the same pattern. Therefore, the first action is to
    # change thisin the datafram by the following relabeling: df['zone']='nz' for all rows where df['name']=carry
    # and df['zone']=oz

    df.loc[df[(df['name']=='carry') & (df['zone'] == 'oz')].index, 'zone'] = 'nz' # make all carries  into oz begin in nz
    # Turn the labels for zone and play_zone relative to team_1.
    df.loc[df[(df['zone']=='oz') & (df['team_in_possession'] == team_2)].index, 'zone'] = 'changed_dz' #use a temporary label
    df.loc[df[(df['zone'] == 'dz') & (df['team_in_possession'] == team_2)].index, 'zone'] = 'oz'
    df.loc[df[(df['zone'] == 'changed_dz') & (df['team_in_possession'] == team_2)].index, 'zone'] = 'dz'
    df.loc[df[(df['play_zone'] == 'oz') & (df['team_in_possession'] == team_2)].index, 'play_zone'] = 'changed_dz' # use a temporary label
    df.loc[df[(df['play_zone'] == 'dz') & (df['team_in_possession'] == team_2)].index, 'play_zone'] = 'oz'
    df.loc[df[(df['play_zone'] == 'changed_dz') & (df['team_in_possession'] == team_2)].index, 'play_zone'] = 'dz'
    if team_1 == home_team:
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hoz'].index, 'zone'] = 'oz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hoz'].index, 'play_zone'] = 'oz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hdz'].index, 'zone'] = 'dz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hdz'].index, 'play_zone'] = 'dz'
    else:
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hoz'].index, 'zone'] = 'dz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hoz'].index, 'play_zone'] = 'dz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hdz'].index, 'zone'] = 'oz'
        faceoffs.loc[faceoffs[faceoffs['type'] == 'hdz'].index, 'play_zone'] = 'oz'


    #df = pd.concat([df,faceoffs])
    #df.sort_values('sl_id', inplace=True)
    res = [(idx,) + tuple(a) for idx,a in df[['name','zone','play_zone','team_in_possession', 'team_id', 'game_time']].iterrows()]
    res_full = [k.to_dict() for idx,k in df.iterrows()]
    zone_transition_events = [(i, r) for i, r in enumerate(res) if r[2] != r[3]]
    zone_transition_events_full = [r for r in res_full if r['zone'] != r['play_zone']]
    new_row_ctr=0

    # For each zone transitioing event (zte), add an event before the zte. This added event is a copy of the zte but with
    # the label for play_zone is set to the same as zone.
    for idx, e in zone_transition_events:
        new_row = (e[0], e[1], e[2], e[2], e[4], e[5], e[6])
        res.insert(idx + new_row_ctr, new_row)
        new_row_ctr += 1

    new_row_ctr=0
    for e in zone_transition_events_full:
        new_item = copy.copy(e)
        new_item['play_zone'] = new_item['zone']
        res_full.insert(int(new_item['sl_id']) + new_row_ctr, new_item)
        new_row_ctr += 1

    res_zipped= list(zip(res[0:-1], res[1:]))
    res_zipped_full = list(zip(res_full[0:-1], res_full[1:]))
    res_final = []
    res_final_full  = []
    for r in res_zipped:
        if r[0][4] == team_1:
            new_item = (r[0][0], r[0][1], r[1][1], r[0][2],r[1][2],r[0][4], r[0][5],r[1][6])
        else:
            new_item = (r[0][0], r[0][1], r[1][1], r[0][2], r[1][2], r[0][4], r[0][5], r[0][6])
        res_final.append(new_item)
    #res_final = [(r[0][0], r[0][1], r[1][1], r[0][2],r[1][2],r[0][4], r[0][5],r[1][6]) for r in res_zipped if r[0][4] == team_1]



    all_entries = [idx for idx in res_final if idx[3] != 'oz' and idx[4] == 'oz']
    all_exits = [idx for idx in res_final if idx[3] == 'oz' and idx[4] != 'oz']

    res_team_1 = []
    oz_faceoffs = [(idx,) + tuple(a) for idx, a in faceoffs[faceoffs['zone'] == 'oz'][
        ['name', 'zone', 'play_zone', 'team_in_possession', 'team_id', 'game_time']].iterrows()]

    for entry in all_entries[:min(len(all_entries), len(all_exits))]:
        exit = all_exits[[x for x, val in enumerate(all_exits) if val > entry][0]]
        entry_type = entry[1] if entry[5] == team_1 else 'self_entry'

        entry_time = entry[7]
        exit_time = exit[7]
        duration = round(float(exit_time - entry_time), 4)
        ozfos = [fo[-1] for fo in oz_faceoffs if fo[0] in range(entry[0], exit[0])]
        current_time = entry_time
        durations = []
        if len(ozfos) > 0:
            for fo_time in ozfos:
                durations.append(round(float(fo_time - current_time), 4))
                current_time = fo_time
            durations.append(round(float(exit_time - current_time), 4))


        res_team_1.append([entry[0], exit[0], entry_type, entry_time, exit_time, duration, durations])

    # oz_faceoffs = list(faceoffs[faceoffs['zone'] == 'oz'].index)
    oz_faceoffs = [(idx,) + tuple(a) for idx, a in faceoffs[faceoffs['zone'] == 'oz'][['name', 'zone', 'play_zone', 'team_in_possession', 'team_id', 'game_time']].iterrows()]
    # oz_faceoffs_indexes = list(oz_faceoffs.index)
    # res_with_fo_split = []
    # for r in res_team_1:
    #     fos = [r[0]] + [f for f in oz_faceoffs_indexes if f in range(r[0], r[1])] +r[1]
    #     new_splits = []
    #     first_event = r[0]
    #     while len(fos)>0:
    #         res_with_fo_split.append()
    #     current_idx = r[0]
    #     #for k in fos:



    return res_team_1, all_entries, all_exits, res_full




def controlled_entries_into_own_dz(df):
    carries_into_own_dz = df.query(f"is_possession_event == {1.0}")
    a = carries_into_own_dz.query(f"zone == 'nz' ")
    b = carries_into_own_dz.query(f"zone == 'dz' ")
    indexes = [idx for idx in a.index if idx+1 in b.index]
    indexes = [idx for idx in indexes if a.loc[idx]['possession_id'] == b.loc[idx+1]['possession_id']]
    return df.loc[indexes]

def controlled_exits_from_own_oz(df):
    carries_out_of_own_oz = df.query(f"is_possession_event == {1.0}")
    a = carries_out_of_own_oz.query(f"zone == 'oz' ")
    b = carries_out_of_own_oz.query(f"zone == 'nz' ")
    indexes = [idx for idx in a.index if idx+1 in b.index]
    indexes = [idx for idx in indexes if a.loc[idx]['possession_id'] == b.loc[idx+1]['possession_id']]
    return df.loc[indexes]

def get_oz_rallies(df, teams=None, raw_data = False):
    nan = np.nan
    if teams is None:
        teams = df.query("team_in_possession not in [@nan, 'None']").team_in_possession.unique()

    oz_rallies = {}
    all_entries_index = {}
    all_exits_index = {}
    pass_types = ['ozentry', 'ozentrystretch', 'ozentryoffboards']
    df = clean(df,'name')
    t = time.time()
    for team in teams:

        team_possessions = df.query("team_in_possession == @team")# and manpower_situation == 'evenStrength'")

        dumpins = team_possessions.query("name == 'dumpin' and outcome == 'successful' ")

        controlled = team_possessions.query("name == 'carry' and zone == 'oz'")

        passes = team_possessions.query("name == 'pass' and type in @pass_types and outcome == 'successful' ")

        #faceoffs = team_possessions.query("type in ['faceoff', 'faceoffcontested'] and zone == 'oz'")

        #self_entries = controlled_entries_into_own_dz(team_possessions)
        #print(time.time() - t)

        #Mark as selfentry in the origingal dataframe since selfentry is not identifyable with
        #Sportlogiq standard tags
        #df.loc[self_entries.index, 'name'] = "selfentry"

        k = []

        all_entries = controlled+passes+dumpins # + self_entries + faceoffs
        oppossing_team_possessions = df.query("team_in_possession != @team")
        outlet_passes = oppossing_team_possessions.query("name == 'pass' and type == 'outlet' ")
        dumpouts = oppossing_team_possessions.query("name == 'dumpout'")
        controlled_exits = oppossing_team_possessions.query("name == 'carry' and zone == 'dz'")
        # whistles = df.query("name" == "whistle")
        # controlled_exits_out_of_own_oz = controlled_exits_from_own_oz(team_possessions)

        all_exits = outlet_passes + dumpouts + controlled_exits #+ controlled_exits_out_of_own_oz
        last_event = df.index[-1]
        entry_index = list(all_entries.index)
        exit_index = list(all_exits.index)
        exit_index.append(last_event)  #Make sure the last entry has a matching exit if game ends in OZ
        oz_rallies_entry_exit = []

        for entry in entry_index:
            exit = exit_index[[x for x,val in enumerate(exit_index) if val > entry][0]]
            oz_rallies_entry_exit.append([entry, exit])

        oz_rallies_team = []

        for rally in oz_rallies_entry_exit:
            t=time.time()
            records = df.loc[rally[0]:rally[1]]
            records_dict = records.to_dict(orient='records')
            oz_rallies_team.append(records_dict) #copy.deepcopy(records_dict))


        oz_rallies[team] = oz_rallies_team
        all_entries_index[team] = list(all_entries.index)
        all_exits_index[team] = list(all_exits.index)
    if raw_data:
        return oz_rallies, all_entries_index, all_exits_index
    return oz_rallies

def entry_positions(oz_rallies):
    for rally in oz_rallies:
        entry_df = pd.DataFrame(rally)
        position = entry_df.iloc[0]

def compute_entry_statistics(entries):
    rally_stats = []
    for entry in entries:
        rally_stat = {}
        entry_df = pd.DataFrame(entry)
        rally_stat['type'] = entry_df.iloc[0]['name']
        rally_stat['time_entry'] = int(entry_df.iloc[0].game_time)
        rally_stat['time_exit'] = int(entry_df.iloc[-1].game_time)
        rally_stat['position_y'] = round(float(entry_df.iloc[0]['x_coordinate']), 2)
        rally_stat['position_x'] = round(float(entry_df.iloc[0]['y_coordinate']), 2)
        rally_stat['period'] = int(entry_df.iloc[0]['period'])
        rally_stat['duration'] = round(float(rally_stat['time_exit']) - float(rally_stat['time_entry']), 2)
        rally_stat['shots'] = compute_time_to_shots(entry_df)
        rally_stat['number_shots'] = len(rally_stat['shots']) if len(rally_stat['shots']) > 0 else None
        rally_stats.append(rally_stat)
    return rally_stats

def compute_time_to_shots(entry):
    entry_df = pd.DataFrame(entry)
    entry_time = entry_df.iloc[0].game_time
    shots = entry_df.query("name == 'shot'")
    number_shots = shots.shape[0]
    shot_list = []
    shot_full_stat = []
    for shot in shots.index:
        # shot_x = shots.loc[shot].x_coordinate
        # shot_y = shots.loc[shot].y_coordinate
        shot_list.append(int(shots.loc[shot].game_time - entry_time))
        # shot_full_stat.append({'shot_time': shots.loc[shot].game_time - entry_time, 'shot_x':shot_x, 'shot_y':shot_y})

    return shot_list
# Deprecated
def time_entry_to_shots(entries):
    entries_with_tts = []
    for entry in entries:
        entry_df = pd.DataFrame(entry)
        entry_type = entry_df.iloc[0]['name']
        entry_time = entry_df.iloc[0].game_time
        exit_time = entry_df.iloc[-1].game_time
        entry_x = entry_df.iloc[0]['x_coordinate']
        entry_y = entry_df.iloc[0]['y_coordinate']
        period = entry_df.iloc[0]['period']
        shots = entry_df.query("name == 'shot'")
        number_shots = shots.shape[0]
        shot_list = []
        shot_full_stat = []
        for shot in shots.index:
            # shot_x = shots.loc[shot].x_coordinate
            # shot_y = shots.loc[shot].y_coordinate
            shot_list.append(shots.loc[shot].game_time - entry_time)
            # shot_full_stat.append({'shot_time': shots.loc[shot].game_time - entry_time, 'shot_x':shot_x, 'shot_y':shot_y})
        rally_stat = {}
        rally_stat['entry_type'] = entry_type
        rally_stat['entry_time'] = float(entry_time)
        rally_stat['exit_time'] = float(exit_time)
        rally_stat['duration'] = round(float(exit_time - entry_time), 2)
        rally_stat['time_to_shots'] = shot_list
        # rally_stat['shot_full_stat'] = shot_full_stat
        rally_stat['entry_x'] = entry_x
        rally_stat['entry_y'] = entry_y
        rally_stat['period'] = int(period)
        # if len(shot_full_stat) == 0:
        #     rally_stat['first_shot_x'] = None
        #     rally_stat['first_shot_y'] = None
        # else:
        #     rally_stat['first_shot_x'] = shot_full_stat[0]['shot_x']
        #     rally_stat['first_shot_y'] = shot_full_stat[0]['shot_y']

        if len(shot_list) == 0:
            rally_stat['time_to_first_shot'] = None
        else:
            rally_stat['time_to_first_shot'] = shot_list[0]

        entries_with_tts.append({'rally_stat': rally_stat, 'rally_events': entry})
        return entries_with_tts



# def time_entry_to_shot(df=None, team=None):
#     pass_types = ['ozentry', 'ozentrystretch', 'ozentryoffboards']
#     df = clean(df,'name')
#     team_possessions = df.query("teamInPossession == @team and manpowerSituation == 'evenStrength'")
#     dumpins = team_possessions.query("name == 'dumpin'")
#     controlled = team_possessions.query("name == 'carry' and zone == 'oz'")
#     passes = team_possessions.query("name == 'pass' and type in @pass_types")
#     all_entries = controlled+passes+dumpins
#
#     ## Print out times for debugging
#     for e in (all_entries.index):
#         t = df.iloc[e]['gameTime']
#         m, s = divmod(round(t), 60)
#         print(str(m), ' ', str(round(s)))
#     oppossing_team_possessions = df.query("teamInPossession != @team")
#     outlet_passes = oppossing_team_possessions.query("name == 'pass' and type == 'outlet'")
#     dumpouts = oppossing_team_possessions.query("name == 'dumpout'")
#     controlled_exits = oppossing_team_possessions.query("name == 'carry' and zone == 'dz'")
#     all_exits = outlet_passes + dumpouts + controlled_exits
#
#     last_event = df.index[-1]
#     entry_index = list(all_entries.index)
#     exit_index = list(all_exits.index)
#     exit_index.append(last_event)  #Make sure the last entry has a matching exit if game ends in OZ
#     oz_rallies = []
#     oz_stats = []
#     for entry in entry_index:
#         exit = exit_index[[x for x,val in enumerate(exit_index) if val > entry][0]]
#         oz_rallies.append([entry, exit])
#
#     for rally in oz_rallies:
#         records = df.iloc[rally[0]:rally[1]+1]
#         entry_type = records.iloc[0]['name']
#         print(entry_type)
#         entry_time = records.iloc[0].gameTime
#         shots = records.query("name == 'shot'")
#         number_shots = shots.shape[0]
#         shot_list = []
#         for shot in shots.index:
#             shot_list.append(shots.loc[shot].gameTime - entry_time)
#
#         rally_stat = {}
#         rally_stat['entry_type'] = entry_type
#         rally_stat['entry_time'] = entry_time
#         rally_stat['time_to_shots'] = shot_list
#         if len(shot_list) == 0:
#             rally_stat['time_to_first_shot'] = None
#         else:
#             rally_stat['time_to_first_shot'] = shot_list[0]
#
#
#         oz_stats.append(rally_stat)
#     return oz_stats

def shot_assist(df=None, filename=None, player_id=None):
    passes_and_shots = df[(df['name'] == 'pass') + (df['name'] == 'shot')]
    successful_passes_and_shots = passes_and_shots.loc[passes_and_shots['outcome'] == 'successful']
    shots_idx = list(successful_passes_and_shots['name'] == 'shot')
    shot_assists_idx = shots_idx[1:] + [False]
    shot_assists = successful_passes_and_shots[shot_assists_idx]
    player_shot_assists = shot_assists[shot_assists['playerRefe]enceId'] == player_id]
    return player_shot_assists.shape[0]

def player_on_ice(df, player_id):
    global APOI
    all_players_on_ice = (df.teamForwardsOnIceRefs + \
                           df.teamDefencemenOnIceRefs + \
                           str(df.teamGoalieOnIceRef) + \
                           df.opposingTeamForwardsOnIceRefs + \
                           df.opposingTeamDefencemenOnIceRefs + \
                           str(df.opposingTeamGoalieOnIceRef)).dropna()

    df = df.loc[all_players_on_ice.index]
    if APOI is None:
        APOI = [re.sub("[^0-9]", " ", s) for s in all_players_on_ice]
    return df[[player_id in on_ice for on_ice in APOI]]

def get_player_ids(df=None, filename=None, team=None):
    players = list(df.query("team == @team").playerReferenceId.astype({'playerReferenceId': 'int'}).unique())
    return players


def add_event_durations(df=None):
    game_times=df['gameTime']
    event_duration = list(np.array(game_times)[1:] - np.array(game_times)[0:-1])
def time_on_ice(df=None, player_id=None):
    game_times = df['gameTime']
    event_duration = list(np.array(game_times)[1:] - np.array(game_times)[0:-1])
    event_duration.append(0)

    # event_duration = list((np.array(game_times)[2:] - np.array(game_times)[0:-2]) / 2)
    # event_duration.insert(0,0)
    # event_duration.append(0)
    # event_duration_pre = event_duration.copy()
    # event_duration_pre.insert(0,0)
    # event_duration_pre.pop(-1)

    woi = player_on_ice(df, str(player_id))

    # woi_index = list(woi.index)
    # woi_pad_pre = [p - 1 for p in woi_index]
    # woi_pad_post = [p + 1 for p in woi_index]
    # woi_padded_pre = list(set(woi_index).union(set(woi_pad_pre)))
    # woi_padded_post = list(set(woi_index).union(set(woi_pad_post)))
    # woi_padded_pre[0] = max(0,woi_padded_pre[0])
    # woi_padded_pre[-1] = min(df.shape[0], woi_padded_pre[-1])
    # woi_padded_post[0] = max(0,woi_padded_post[0])
    # woi_padded_post[-1] = min(df.shape[0], woi_padded_post[-1])
    # woi_pre = df.iloc[woi_padded_pre]
    # woi_post = df.iloc[woi_padded_post]

    toi = sum(np.array(event_duration)[list(woi.index)])
    #toi_pre = sum(np.array(event_duration)[list(woi_pre.index)])
    #toi_post = sum(np.array(event_duration)[list(woi_post.index)])
    m,s = divmod(round(toi),60)
    #m_pre, s_pre = divmod(round(toi_pre),60)
    #m_post, s_post = divmod(round(toi_post), 60)
    return f'{m:02d}min {s:02d} sek' #, f'{m_pre:02d}min {s_pre:02d} sek', f'{m_post:02d}min {s_post:02d} sek'

def pim(df=None, filename=None, player_id=None):
    #df = pd.read_csv(filename)
    penalties = df.loc[df['name'] == 'penalty']
    player_penalties = penalties.loc[penalties['playerReferenceId'] == player_id]
    pim = player_penalties.shape[0] * 2
    return pim

def plus_minus(df=None, player_id=None, team=None):
    in_possession = df.loc[df['teamInPossession'] == team]
    not_in_possession = df.loc[~(df['teamInPossession'] == team)]
    plus_goals = in_possession.loc[in_possession['name'] == 'goals']
    plus_goals = plus_goals.loc[plus_goals['outcome'] == 'successful']
    minus_goals = not_in_possession.loc[not_in_possession['name'] == 'goal']
    minus_goals = minus_goals.loc[minus_goals['outcome'] == 'successful']
    player_plus = plus_goals.loc[[str(player_id) in k for k in [re.sub("[^0-9,',']", "", s) for s in list(
        plus_goals['teamForwardsOnIceRefs'] +
        plus_goals['teamDefencemenOnIceRefs'])]]]
    player_minus = minus_goals.loc[[str(player_id) in k for k in [re.sub("[^0-9,',']", "", s) for s in list(
            minus_goals['opposingTeamForwardsOnIceRefs'] +
            minus_goals['opposingTeamDefencemenOnIceRefs'])]]]

    return player_plus.shape[0] - player_minus.shape[0]

def get_player_info(df=None,filename=None, player_id=None):
    #df = pd.read_csv(filename)
    player = df.loc[df['playerReferenceId'] == player_id]
    player_name = player.playerFirstName.unique()[0] + ' ' + player.playerLastName.unique()[0]
    player_number = int(player.playerJersey.unique()[0])
    player_position = player.playerPosition.unique()[0]
    return [player_name, player_number, player_position]

def get_teams(filename=None):
    df = pd.read_csv(filename)
    nan = np.nan
    teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    return teams

def generate_summary(filename=None, df=None, team=None):
    global APOI
    APOI = None
    if df is None:
        df = pd.read_csv(filename)
    nan = np.nan
    teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    team_1 = generate_summary_for_team(df=df, team=teams[0])
    team_2 = generate_summary_for_team(df=df, team=teams[1])
    #team_1.to_csv('team_1.csv')
    #team_2.to_csv('team_2.csv')
    return team_1, team_2



def entry_histogram(entries, ax=None, ax2=None, team=''):

    ax = ax or plt.gca()
    ax2 = ax2 or plt.gca()

    def func(pct, entries):
        absolute = int(np.round(pct / 100. * np.sum(entries)))
        #return "{:d}\n({:.0f}%)".format(absolute, pct)
        return "{:d}".format(absolute)

    labels = ['Passes', 'Dumpins', 'Carries']
    total = float(len(entries))
    lead_to_shot = float(len([e for e in entries if e['time_to_first_shot']]))
    passes = len([e for e in entries if e['entry_type'] == 'pass'])
    passes_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'pass'])
    dumpins = len([e for e in entries if e['entry_type'] == 'dumpin'])
    dumpins_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'dumpin'])
    carries = len([e for e in entries if e['entry_type'] == 'carry'])
    carries_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'carry'])
    total = float(len(entries) - lead_to_shot)
    data = [passes, dumpins, carries]
    captions=[str(carries) + '(' + str(carries_with_shot) + ')',
              str(dumpins) + '(' + str(dumpins_with_shot) + ')',
              str(passes) + '(' + str(passes_with_shot) + ')']
    entries_with_shot = [passes_with_shot, dumpins_with_shot, carries_with_shot]
    ax.pie(data, labels=labels, autopct=lambda pct: func(pct, data), textprops=dict(color="k", size=10),
            shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.title.set_text('All Entries')
    ax2.title.set_text('Shot Generating Entries')
    ax2.pie(entries_with_shot, labels=labels, autopct=lambda pct: func(pct, entries_with_shot), textprops=dict(color="k", size=10),
            shadow=True, startangle=90)
    ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    return ax

def oge_histogram(entries, ax=None, team=''):
    ax = ax or plt.gca()
    total = len(entries)
    entries = [e['time_to_first_shot'] for e in entries if e['time_to_first_shot']]
    interval = 3
    num_bins = math.ceil(max(entries) / interval)
    last_bin = num_bins * interval
    bins = [i for i in range(0,last_bin+1, interval)]
    labels = []
    for i in bins:
        label = str(i) + ' to ' + str(i + interval) + ' sec '
        labels.append(label)

    ax.hist(np.array(entries), histtype='barstacked', rwidth=0.8, density=False, align='mid', bins=bins, orientation='horizontal', range=(0, max(entries)))
    plt.sca(ax)
    plt.yticks([b+interval/2 for b in bins[:-1]], labels[:-1], rotation='horizontal', horizontalalignment='right')
    plt.xlabel('Of '+ str(total) + ' entries lead ' + str(len(entries)) + ' to at least one shot')
    #plt.title(team)
    return ax

# def generate_entry_statistics(filename=None, df=None, team=None):
#
#     try:
#         entry_graphics = []
#         APOI = None
#         if df is None:
#             df = pd.read_csv(filename)
#         nan = np.nan
#         teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
#         team_1 = time_entry_to_shot(df=df, team=teams[0])
#         team_2 = time_entry_to_shot(df=df, team=teams[1])
#         return (team_1, team_2), teams
#     except:
#         return None
#
#     #     fig = plt.figure(tight_layout=True)
#     #     gs = gridspec.GridSpec(2, 2)
#     #     ax0 = fig.add_subplot(gs[0,0])
#     #     ax1 = fig.add_subplot(gs[0,1])
#     #     ax2 = fig.add_subplot(gs[1, :])
#     #     fig.set_size_inches(10,10)
#     #     entry_histogram(team_1, ax=ax0, ax2=ax1)
#     #     oge_histogram(team_1, ax=ax2, team=teams[0])
#     #     fig.suptitle(teams[0], fontsize=20)
#     #     fig.tight_layout(pad=1.0)
#     #     fig.savefig('static/images/entrystats_team_1.png', dpi=100)
#     #     img = io.BytesIO()
#     #     fig.savefig(img, format='png')
#     #     entry_graphics.append(img)
#     #
#     #     fig = plt.figure(tight_layout=True)
#     #     gs = gridspec.GridSpec(2, 2)
#     #     ax0 = fig.add_subplot(gs[0,0])
#     #     ax1 = fig.add_subplot(gs[0,1])
#     #     ax2 = fig.add_subplot(gs[1, :])
#     #     fig.set_size_inches(10, 10)
#     #     entry_histogram(team_2, ax=ax0, ax2=ax1)
#     #     oge_histogram(team_2, ax=ax2, team=teams[1])
#     #     fig.suptitle(teams[1], fontsize=20)
#     #     fig.tight_layout(pad=1.0)
#     #     fig.savefig('static/images/entrystats_team_2.png', dpi=100)
#     #
#     #     img = io.BytesIO()
#     #     fig.savefig(img, format='png')
#     #     entry_graphics.append(img)
#     # except:
#     #     print("Could no compute entry statistics from the provided file")
#     #     teams = None
#     #     entry_graphics = None
#     #
#     #
#     # return teams, entry_graphics

def player_turnovers(df=None, player_id=None, failing_team=None):
    clean = df['isLastPlayOfPossession'].dropna()
    clean = df.iloc[clean.index]
    possession_plays = clean.query("playerReferenceId == @player_id")
    playtypes = ['pass', 'shot', 'dumpin', 'dumpout', 'puckprotection']
    entries = ['ozentry', 'ozentryoffboards', 'ozentrystretch', 'outlet', 'outletoffboards']
    possession_plays = possession_plays.query("name in @playtypes")
    successful_plays = possession_plays.query("outcome == 'successful'").shape[0]
    failed_plays = possession_plays.query("outcome == 'failed'").shape[0]
    total_plays = successful_plays + failed_plays

    step1 = df[['currentPossession', 'isLastPlayOfPossession', 'teamInPossession']].dropna()
    step2 = df.iloc[step1.currentPossession.drop_duplicates().index]
    l1 = step2.teamInPossession.tolist()
    l2 = step2.teamInPossession.tolist()[1:]
    change_in_possession = [a != b for a, b in zip(l1, l2)]
    change_in_possession.append(False)
    step2.insert(step2.shape[1], 'lastPossessionInRally', change_in_possession)
    step3 = df['currentPossession'].dropna()
    step3 = df.iloc[step3.index]
    last_plays = step3.query("isLastPlayOfPossession and teamInPossession == @failing_team and not type in @entries")
    lost_possessions = pd.merge(step2, last_plays, on='currentPossession')
    lost_possessions = lost_possessions.query("lastPossessionInRally")
    player_lost_possessions = lost_possessions.query("outcome_y == 'failed' and playerReferenceId_y == @player_id")
    player_lost_possessions = player_lost_possessions.query("type_y not in @entries")

    turnover_rate = -1 #set as default to skip an else-clause below
    if total_plays > 0:
        turnover_rate = float(player_lost_possessions.shape[0]) / float(total_plays)
    turnover_rate = round(100*turnover_rate)
    takeaways = clean.query("isPossessionBreaking and playerReferenceId == @player_id")

    return turnover_rate, takeaways.shape[0], successful_plays+failed_plays, successful_plays, failed_plays

    step3 = step2.teamInPossession

    step2 = step1[['currentPossession']].unique()
    last_play = df.query("isLastPlayOfPossession")
    possessions = df.loc[df.currentPossession.drop_duplicates().index]

    c = df[['currentPossession', 'isLastPlayOfPossession', 'teamInPossession']].dropna().query("isLastPlayOfPossession")

    # game_times = df['gameTime']
    # event_duration = list(np.array(game_times)[1:] - np.array(game_times)[0:-1])
    clean = df['isPossessionBreaking'].dropna()
    df = df.iloc[clean.index]
    possession_breaking = df.query("isPossessionBreaking")
    last_play = df.query("isLastPlayOfPossession")
    turn_o_a = pd.merge(possession_breaking, last_play, on='currentPossession', suffixes=('_ta', '_to'))

    player_to = turn_o_a.query("playerReferenceId_to == @player_id").shape[0]
    player_ta = turn_o_a.query("playerReferenceId_ta == @player_id").shape[0]
    return player_to, player_ta

def generate_summary_for_team(df=None, filename=None, team=None):

    p = time_entry_to_shot(df=df, team=team)
    tor, ta ,t, s, f = player_turnovers(df, int(29862), failing_team='Sweden Sweden')

    players = get_player_ids(df=df, team=team)
    print(players)
    fields = ['Name', 'Number','Position','TOI','Shots on Net from slot (ES)',
              'Shots On Net From Outside (ES)', 'Shot Assists (ES)', 'Shots On Net For WOI (ES)',
              'Shots On Net Against WOI (ES)','Passes to Slot FOR WOI (ES)', 'Passes to slot AGAINST WOI (ES)', 'OGP/20',
              'Total Possessions', 'Successful Possessions', 'Failed Possessions', 'True Turnovers (percent)', 'Takeaways','Goals', 'Assists', 'Points', 'Penalty Minutes','Blocked Shots', 'Plus/Minus','Faceoffs +', 'Faceoffs Total', 'Faceoffs percent',
              'Shots On Net (PP)', 'Shot attempts (PP)', 'Shots On Net AGAINST (PP)', 'Shot Attempts AGAINST (PP)']

    #to, ta = turnovers(df=df, player_id=int(25691))

    output = pd.DataFrame(columns=fields)

    for player_id in players:
        # Begin with Even Strength metrics
        even_strength = df.query("manpowerSituation == 'evenStrength'")
        personal = even_strength.query("playerReferenceId == @player_id")
        #s = time.time()
        #toi = time_on_ice(df=df, player_id=player_id)
        toi = time_on_ice(df=df, player_id=player_id)
        #t = time.time()
        #print("Executiontime for toi: ", t-s)
        woi = player_on_ice(df, str(player_id))
        woi = woi.query("manpowerSituation == 'evenStrength' ")
        shots_from_slot_es = personal.query("name == 'shot' and outcome=='successful' and type=='slot'").shape[0]
        shots_from_outside_es = personal.query("name == 'shot' and outcome=='successful' and type=='outside'").shape[0]
        shots_woi_for_es = woi.query("name == 'shot' and outcome == 'successful' and teamInPossession == @team").shape[0]
        shots_woi_against_es = woi.query("name == 'shot' and outcome == 'successful' and teamInPossession != @team").shape[0]
        shot_assists = shot_assist(df=df, player_id=player_id)
        passes_to_slot_for_woi = woi.query(
            "name == 'pass' and teamInPossession == @team and outcome == 'successful' and type=='slot'").shape[0]
        passes_to_slot_against_woi = woi.query(
            "name == 'pass' and teamInPossession != @team and outcome == 'successful' and type=='slot'").shape[0]
        ogp_20=0
        #successful_possession_plays = personal.query("isPossessionEvent and outcome == 'successful'").shape[0]
        #total_possession_plays = personal.query("isPossessionEvent").shape[0]
        #turnover_rate = float(successful_possession_plays) / float(total_possession_plays+0.00000001)
        turnover_rate, takeaways, total_possessions, successful_possessions, failed_possessions = \
            player_turnovers(df=df, player_id=player_id, failing_team=team)

        personal = df.query("playerReferenceId == @player_id")
        p_m = plus_minus(df=df, player_id=player_id,team=team)


        faceoffs_total_df = personal.query("name == 'faceoff' ")
        faceoffs_won_df = faceoffs_total_df.query("outcome == 'successful'")

        faceoffs_total = faceoffs_total_df.shape[0]
        faceoffs_won = faceoffs_won_df.shape[0]
        if faceoffs_total > 0:
            faceoffs_percent = float(faceoffs_won)/float(faceoffs_total)
            faceoffs_percent = round(100*faceoffs_percent)
        else:
            faceoffs_percent = -1

        #faceoffs_won = 0
        #faceoffs_total = 0
        #faceoff_percent = 0
        goals = personal.query("name == 'goal'").shape[0]
        assists = personal.query("name == 'assist'").shape[0]
        points = goals + assists
        penalties = pim(df=df, player_id=player_id)
        blocked_shots = personal.query("name == 'block' and type == 'shot'").shape[0]
        shots_on_net_pp = personal.query(
            "name == 'shot' and outcome == 'successful' and manpowerSituation == 'powerPlay'").shape[0]
        shot_attempts_pp = personal.query(
            "name == 'shot' and outcome != 'successful' and manpowerSituation == 'powerPlay'").shape[0]
        woi = player_on_ice(df, str(player_id))
        shots_on_net_against_sh = woi.query(
            "name == 'shot' and outcome == 'succesful' and manpowerSituation == 'powerPlay' and team != @team").shape[0]
        shot_attempts_against_sh = woi.query(
            "name == 'shot' and manpowerSituation == 'powerPlay' and team != @team").shape[0]
        player_info = get_player_info(df=df, player_id=player_id)
        #print(player_info,' ', player_id, ' ', toi)
        new_row = player_info + [toi, shots_from_slot_es, shots_from_outside_es, shot_assists, shots_woi_for_es, shots_woi_against_es,
                   passes_to_slot_for_woi, passes_to_slot_against_woi, ogp_20, total_possessions,
                   successful_possessions, failed_possessions, turnover_rate, takeaways,
                   goals, assists, points, penalties, blocked_shots, p_m, faceoffs_won, faceoffs_total, faceoffs_percent,
                   shots_on_net_pp, shot_attempts_pp, shots_on_net_against_sh, shot_attempts_against_sh]

        output.loc[len(output.index)] = new_row
    return output


def line_toi_when_goal(game_number):
    return -1

