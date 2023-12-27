import pandas as pd
import re
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.font_manager import FontProperties
from matplotlib import colors
import io
import os
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
APOI = None
from scipy.ndimage import interpolation
import math
import db_tools
import entries

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
       'players_on_ice': 'apoi', 'player_on_ice':'apoi'}

inv_map = {map[k]: k for k in map.keys()}
def clean(df,col):
    clean = df[col].dropna()
    return df.iloc[clean.index]

def time_entry_to_shot(df=None, team=None, end_on_whistle = True, only_goals=True):
    pass_types = ['ozentry', 'ozentrystretch', 'ozentryoffboards']
    # df = clean(df,'name')
    team_possessions = df.query("teamInPossession == @team and manpowerSituation == 'evenStrength'")
    dumpins = team_possessions.query("name == 'dumpin'")
    controlled = team_possessions.query("name == 'carry' and zone == 'oz'")
    passes = team_possessions.query("name == 'pass' and type in @pass_types")
    all_entries = controlled+passes+dumpins

    ## Print out times for debugging
    # for e in (all_entries.index):
    #     t = df.iloc[e]['gameTime']
    #     m, s = divmod(round(t), 60)
    #     print(str(m), ' ', str(round(s)))
    oppossing_team_possessions = df.query("teamInPossession != @team")
    outlet_passes = oppossing_team_possessions.query("name == 'pass' and type == 'outlet'")
    dumpouts = oppossing_team_possessions.query("name == 'dumpout' and outcome == 'successful'")
    controlled_exits = oppossing_team_possessions.query("name == 'carry' and zone == 'dz'")
    faceoffs = df.query("name == 'faceoff'")
    all_exits = outlet_passes + dumpouts + controlled_exits + faceoffs

    last_event = df.index[-1]
    entry_index = list(all_entries.index)
    exit_index = list(all_exits.index)
    exit_index.append(last_event)  #Make sure the last entry has a matching exit if game ends in OZ
    oz_rallies = []
    oz_stats = []
    for entry in entry_index:
        exit = exit_index[[x for x,val in enumerate(exit_index) if val > entry][0]]
        oz_rallies.append([entry, exit])

    for rally in oz_rallies:
        records = df.iloc[rally[0]:rally[1] + 1]
        # If end_on_whistle is set, only look at the events up to the whistle
        if end_on_whistle:
            whistles = records.query("name == 'whistle' or name == 'faceoff'")
            if whistles.shape[0] > 0:
                records = df.iloc[rally[0]:whistles.index[0]]

        entry_type = records.iloc[0]['name']
        #print(entry_type)
        entry_time = records.iloc[0].gameTime
        if not only_goals:
            shots = records.query("name == 'shot'")
        else:
            shots = records.query("name == 'goal' and outcome == 'successful'")

        #print(rally, ' ', shots.shape[0])
        number_shots = shots.shape[0]
        shot_list = []
        for shot in shots.index:
            shot_list.append(shots.loc[shot].gameTime - entry_time)

        rally_stat = {}
        rally_stat['entry_type'] = entry_type
        rally_stat['entry_time'] = entry_time
        rally_stat['time_to_shots'] = shot_list
        if len(shot_list) == 0:
            rally_stat['time_to_first_shot'] = None
        else:
            rally_stat['time_to_first_shot'] = shot_list[0]


        oz_stats.append(rally_stat)
    return oz_stats

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
    colors = [[1.0, 0, 0, 0.7], [0, 1, 0, 0.7], [0, 0, 1.0, 0.7]]
    def func(pct, entries):
        absolute = int(np.round(pct / 100. * np.sum(entries)))
        return "{:d}\n({:.0f}%)".format(absolute, pct)
        #return "{:d}".format(absolute)

    labels = ['','','']#'Passes', 'Dumpins', 'Carries']
    total = float(len(entries))
    lead_to_shot = float(len([e for e in entries if e['time_to_first_shot']]))
    passes = len([e for e in entries if e['entry_type'] == 'pass'])
    passes_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'pass'])
    dumpins = len([e for e in entries if e['entry_type'] == 'dumpin'])
    dumpins_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'dumpin'])
    carries = len([e for e in entries if e['entry_type'] == 'carry'])
    carries_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'carry'])
    total = float(len(entries) - lead_to_shot)
    all_entries = [passes, dumpins, carries]
    captions=[str(passes) + '(' + str(passes_with_shot) + ')',
              str(dumpins) + '(' + str(dumpins_with_shot) + ')',
              str(carries) + '(' + str(carries_with_shot) + ')']
    entries_with_shot = [carries_with_shot, dumpins_with_shot, passes_with_shot]
    entries_no_shot = [carries - carries_with_shot, dumpins - dumpins_with_shot, passes-passes_with_shot]
    #ax.pie(all_entries, labels=labels, autopct=lambda pct: func(pct, all_entries), textprops=dict(color="k", size=10),
    #        shadow=True, startangle=90)

    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('OZ entries with no shots', fontsize=30)
    ax2.axis('equal')
    ax2.set_title('OZ entries generating shots', fontsize=30)
    ax.pie(entries_no_shot, labels=labels, textprops=dict(color="k", size=25),
            shadow=True, startangle=90, colors=colors, autopct=lambda pct: func(pct, entries_no_shot))
    ax2.pie(entries_with_shot, labels=labels, textprops=dict(color="k", size=25),
            shadow=True, startangle=90, colors=colors, autopct=lambda pct: func(pct, entries_with_shot))

    # return ax, ax2

def times_to_first_shot(entries):
    ttfs = [e['time_to_first_shot'] for e in entries if e['time_to_first_shot']]
    return ttfs


def noges_for_types(entries):
    noges = [e for e in entries if not e['time_to_first_shot']]
    noges_dumpins = [e for e in noges if e['entry_type'] == 'dumpin']
    noges_passes = [e for e in noges if e['entry_type'] == 'pass']
    noges_carries = [e for e in noges if e['entry_type'] == 'carry']
    data = np.array([len(noges_passes), len(noges_dumpins), len(noges_carries)])
    cell_text = []
    x_pos = [0,4,8]
    for col in range(3):
        plt.bar(col, data[col], color='red')
        #cell_text.append(['%d' % x for x in data[col]])
def oge_time_to_shot(entries, fig=None, ax=None, max_time=30, interval=3):
    # demo()
    # noges_for_types(entries)
    if fig is None:
        fig = plt.figure(figsize=(40,25))

    ax = fig.add_gridspec(4, 4)
    ax1 = fig.add_subplot(ax[0:2, 3:])
    ax2 = fig.add_subplot(ax[2:, 3:])

    ax3 = fig.add_subplot(ax[0:,0:3])

    entry_histogram(entries, ax=ax1, ax2=ax2)

    #fig=plt.figure(figsize=(15, 10))
    bin_cnt = int(max_time // interval)
    oges = [e for e in entries if e['time_to_first_shot']]
    oges_dumpins = [e for e in oges if e['entry_type'] == 'dumpin']
    oges_passes = [e for e in oges if e['entry_type'] == 'pass']
    oges_carries = [e for e in oges if e['entry_type'] == 'carry']

    noges = [e for e in entries if not e['time_to_first_shot']]
    noges_dumpins = [e for e in noges if e['entry_type'] == 'dumpin']
    noges_passes = [e for e in noges if e['entry_type'] == 'pass']
    noges_carries = [e for e in noges if e['entry_type'] == 'carry']

    dumpins_ttfs = times_to_first_shot(oges_dumpins)
    passes_ttfs = times_to_first_shot(oges_passes)
    carries_ttfs = times_to_first_shot(oges_carries)
    #plt.bar([i for i in range(0,max_time + interval, interval)], dumpins_ttfs)
    #plt.hist([dumpins_ttfs, passes_ttfs, carries_ttfs], range=(0, bin_cnt*interval), width=10, stacked=True)
    counts_c, bins_c = np.histogram(carries_ttfs, range=(0, max_time), bins=bin_cnt)
    counts_d, bins_d = np.histogram(dumpins_ttfs, range=(0, max_time), bins=bin_cnt)
    counts_p, bins_p = np.histogram(passes_ttfs, range=(0, max_time), bins=bin_cnt)

    high_c = len([e for e in oges_carries if e['time_to_first_shot'] > max_time])
    high_d = len([e for e in oges_dumpins if e['time_to_first_shot'] > max_time])
    high_p = len([e for e in oges_passes if e['time_to_first_shot'] > max_time])


    data = np.array([counts_c, counts_d, counts_p])
    data = np.hstack((data, np.array([[high_c], [high_d], [high_p]])))
    # data = np.hstack((data, np.array([[len(noges_carries)], [len(noges_dumpins)], [len(noges_passes)]])))
    columns = [str(int(bins_c[i])) + ' to ' + str(int(bins_c[i+1])) + ' s' for i in range(0, len(bins_c) - 1)] + \
              ['> ' + str(max_time) + ' s'] #+ ['no shots']
    rows = ['carries', 'dumpins', 'passes']
    # colors = plt.cm.BuPu(np.linspace(0, 0.5, len(rows)))
    colors = [[1.0,0,0,0.7], [0,1,0,0.7], [0,0,1.0,0.7]]
    n_rows = len(data)

    index = np.arange(len(columns)) + 0.3
    bar_width = 0.4

    # Initialize the vertical-offset for the stacked bar chart.
    y_offset = np.zeros(len(columns))
    values = np.arange(0, np.max(data)+10, 10)
    value_increment = 1

    # Plot bars and create text labels for the table
    cell_text = []
    plt.axis = ax3
    for row in range(n_rows):
        plt.bar(index, data[row], bar_width, bottom=y_offset, color=colors[row])
        y_offset = y_offset + data[row]
        cell_text.append(['%d' % x for x in data[row]])

    plt.ylabel(f"Number of entries generating a shot within each time interval", fontsize=25)
    plt.yticks(values * value_increment, ['%d' % val for val in values])
    plt.yticks(fontsize=20)
    plt.xticks([])
    # plt.title('Entries Time-To-Shot', fontsize=18, weight='bold')
    # Reverse colors and text labels to display the last value at the top.
    colors = colors[::-1]
    cell_text.reverse()
    rows.reverse()


    the_table = plt.table(cellText=cell_text,
                          rowLabels=rows,
                          rowColours=colors,
                          colLabels=columns,
                          cellLoc='center',
                          loc='bottom',
                          fontsize=20)
    the_table.auto_set_font_size(False)
    for (row, col), cell in the_table.get_celld().items():
        cell.set_text_props(fontproperties=FontProperties(weight='bold', size=20))

    plt.legend(['carries','dumpins','passes'], fontsize=30)
    the_table.scale(1,4)
    #fig.show()
    # plt.show()
    ax1 = plt
    return plt




def oge_histogram_2(entries, ax=None, team=''):
    ax = ax or plt.gca()
    oges = [e['time_to_first_shot'] for e in entries if e['time_to_first_shot']]
    noges = [e for e in entries if not e['time_to_first_shot']]


    intervals = [(0,3),(3,6),(6,9),(9,12), (12,15), (15,18), (18,21), (21,24), (24,27), (27,30),(30, 9999)]
    bin_values = []
    for interval in intervals:
        bin_values.append(len([e for e in oges if e<interval[1] and e>=interval[0]]))
    bin_values.append(len(noges))

    plt.margins(0.01)
    plt.sca(ax)
    labels = []
    # x_ticks=[i[0] for i in intervals]
    # x_ticks.append(33)
    num_el = len(intervals)
    colors = [tuple((1.0 - (float(r)/12.0),0,0,1)) for r in range(0, 12)]
    #colors =11*[(1.0,0.0,0.0, 1.0)] + [(0,0,1.0, 0)]
    x_ticks = [i for i in range(0, len(intervals) + 1)]
    ticklabels=['within ' + str(3+3*x) + ' s ' for x in x_ticks[:-1]]
    ticklabels[-1] = 'within more than 30 s'
    ticklabels.append('entries not generating in shot')
    #ticklabels.append('>30')
    #ax.set_xticklabels(ticklabels)
    plt.bar(x_ticks, bin_values, width=0.95, align='center', color=colors, edgecolor='black')
    plt.xticks(x_ticks)
    ax.set_xticklabels(ticklabels, rotation=90)
    return ax

def oge_histogram(entries, ax=None, team=''):
    # ax = oge_histogram_2(entries, ax, team)
    # oge_histogram_3(entries)
    return ax
    ax = ax or plt.gca()
    total = len(entries)
    entries = [e['time_to_first_shot'] for e in entries if e['time_to_first_shot']]
    interval = 3
    num_bins = math.ceil(max(entries) / interval)
    last_bin = num_bins * interval
    bins = [i for i in range(0,last_bin+1, interval)]
    labels = []

    plt.margins(0.01)
    for i in bins:
        label = str(i) + ' to ' + str(i + interval) + ' sec '
        label = str(i+interval)
        labels.append(label)

    ax.hist(np.array(entries), histtype='barstacked', rwidth=0.95, density=False, align='mid', bins=bins, orientation='vertical', range=(0, max(entries)))
    plt.sca(ax)

    #plt.xticks([b+interval/2 for b in bins[:-1]], labels[:-1], rotation='horizontal', horizontalalignment='right')
    plt.xticks([b + interval for b in bins[:-1]], labels[:-1], rotation='horizontal', horizontalalignment='right')
    #plt.xlabel('Of '+ str(total) + ' entries lead ' + str(len(entries)) + ' to at least one shot')
    plt.xlabel('Time to first shot after offensive zone entry (seconds)')
    plt.ylabel('Entries (#)')
    #plt.title(team)
    return ax

def es_goals_for_team(team, league, season):
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()
    sql = f"select id from event where team_in_possession={team} and name='goal' and outcome='successful' and manpower_situation = 'evenStrength'"
    cursor.execute(sql)
    goals = cursor.fetchall()
    return len(goals)


def generate_entry_statistics_team(team, league, season):
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()
    sql = f"select id from game where home_team_id={team} or away_team_id={team};"
    cursor.execute(sql)
    games = cursor.fetchall()
    game_ids = [g[0] for g in games]
    #game_ids=[4638]
    #game_ids=game_ids[-1:]
    print(game_ids)
    all_tts = []
    for game_id in game_ids:
        sql = f"select home_team_id, away_team_id from game where game.id={game_id};"
        cursor.execute(sql)
        a = cursor.fetchall()
        print('computing game ', (game_ids.index(game_id)), ' of ', str(len(game_ids)), a)
        new_entries = get_entries(game_id, team)
        for entry in new_entries:
            all_tts.append(entry)
    return all_tts
def get_entries(game_id, team_id):
    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()

    sql=f"select * from event where game_id={game_id};"
    cursor.execute(sql)
    events=cursor.fetchall()
    cursor.execute("show columns from event;")
    a=cursor.fetchall()
    column_names=[map[c[0]] for c in a]
    df = pd.DataFrame(events, columns=column_names)
    return df
    # try:
    #     nan = np.nan
    #     df = pd.DataFrame(events, columns=column_names)
    #     #teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    #     tts = entries.time_entry_to_shot(df=df, team=team_id)
    # except:
    #     print('Failed to generate time-to-shot for ', team_id, ' in game ', game_id)
    #     return []
    # return tts

def generate_entry_graphics(tts, team='Team', dir='/'):
    if isinstance(team, int):
        team_name = db_tools.get_team_name(team)
    else:
        team_name=team

    entry_graphics = []
    fig = plt.figure(tight_layout=True)
    gs = gridspec.GridSpec(2, 2)
    ax0 = fig.add_subplot(gs[0,0])
    ax1 = fig.add_subplot(gs[0,1])
    ax2 = fig.add_subplot(gs[1, :])
    fig.set_size_inches(10,10)
    entry_histogram(tts, ax=ax0, ax2=ax1)
    oge_histogram(tts, ax=ax2, team=team_name)
    fig.suptitle(team_name, fontsize=20)
    fig.tight_layout(pad=1.0)
    filename = os.path.join(dir, team_name)
    fig.savefig(filename, dpi=100)
    img = io.BytesIO()
    fig.savefig(img, format='png')
    entry_graphics.append(img)

def generate_entry_statistics(game_id, team=None):

    stats_db = db_tools.open_database()
    cursor = stats_db.cursor()

    sql=f"select * from event where game_id={game_id};"
    cursor.execute(sql)
    events=cursor.fetchall()
    cursor.execute(f"select home_team_id, away_team_id from game where id={game_id};")
    (home_team, away_team) = cursor.fetchall()[0]
    cursor.execute("show columns from event;")
    a=cursor.fetchall()
    column_names=[map[c[0]] for c in a]
    try:
        entry_graphics = []
        APOI = None
        nan = np.nan
        df = pd.DataFrame(events, columns=column_names)
        team_1 = time_entry_to_shot(df=df, team=home_team)
        team_2 = time_entry_to_shot(df=df, team=away_team)

        fig = plt.figure(tight_layout=True)
        gs = gridspec.GridSpec(2, 2)
        ax0 = fig.add_subplot(gs[0,0])
        ax1 = fig.add_subplot(gs[0,1])
        ax2 = fig.add_subplot(gs[1, :])
        fig.set_size_inches(10,10)
        entry_histogram(team_1, ax=ax0, ax2=ax1)
        oge_histogram(team_1, ax=ax2, team=home_team)
        fig.suptitle("Home Team", fontsize=20)
        fig.tight_layout(pad=1.0)
        fig.savefig('static/images/entrystats_team_1.png', dpi=100)
        img = io.BytesIO()
        fig.savefig(img, format='png')
        entry_graphics.append(img)

        fig = plt.figure(tight_layout=True)
        gs = gridspec.GridSpec(2, 2)
        ax0 = fig.add_subplot(gs[0,0])
        ax1 = fig.add_subplot(gs[0,1])
        ax2 = fig.add_subplot(gs[1, :])
        fig.set_size_inches(10, 10)
        entry_histogram(team_2, ax=ax0, ax2=ax1)
        oge_histogram(team_2, ax=ax2, team=away_team)
        fig.suptitle("Visiting Team", fontsize=20)
        fig.tight_layout(pad=1.0)
        fig.savefig('static/images/entrystats_team_2.png', dpi=100)

        img = io.BytesIO()
        fig.savefig(img, format='png')
        entry_graphics.append(img)
    except:
        print("Could no compute entry statistics from the provided file")
        teams = None
        entry_graphics = None


    return [home_team, away_team], entry_graphics

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

