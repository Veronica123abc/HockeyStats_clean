import json
import mpld3
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from collections import defaultdict
import db_tools
import dotenv
import os
import ingest
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo
import cv2
import io
import base64
# import entries
#from generate_entry_statistics import stats_db
import apiv2
dotenv.load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT")

def create_interactive_line_plot(home_wp, away_wp, home_chances, away_chances, filename='hockey_visual3.html'):

    team_strengths=[]
    # Interpolate all intermediate values for the two teams
    for team_wp in [home_wp, away_wp]:
        length = len(team_wp)
        times, values = zip(*team_wp)
        full_time = np.arange(length)
        team_strengths.append(np.interp(full_time, times, values))
    home_strength = team_strengths[0] #  interpolate_strength(home_wp)
    away_strength = team_strengths[1] # interpolate_strength(away_wp)
    game_duration = len(home_wp)
    x = np.arange(game_duration)

    home_y_offsets = [0.0, 10.0, 20.0, 30.0]
    away_y_offsets = [0.0, 10.0, 20.0, 30.0]

    home_team_color = 'blue'
    away_team_color = 'red'
    difference_color = 'black'
    text_color = 'white'
    flag_color = 'black'
    flag_edge = 'white'
    # Calculate y-positions for flags using cycling offsets
    home_flag_ys = [max(home_strength) + home_y_offsets[i % len(home_y_offsets)] for i in range(len(home_chances))]
    away_flag_ys = [-max(away_strength) - away_y_offsets[i % len(away_y_offsets)] for i in range(len(away_chances))]

    # Line plots for strengths
    home_trace = go.Scatter(x=x, y=home_strength, mode='lines', name='Home Team', line=dict(color=home_team_color, width=2))
    away_trace = go.Scatter(x=x, y=-away_strength, mode='lines', name='Away Team', line=dict(color=away_team_color, width=2))
    diff_trace = go.Scatter(x=x, y=home_strength - away_strength, mode='lines', name='Difference', line=dict(color=difference_color, width=4))
    # Marker traces for chances
    shapes = []
    for (t, _), y in zip(home_chances, home_flag_ys):
        shapes.append(dict(
            type='line',
            x0=t, x1=t,
            y0=0, y1=y,
            line=dict(color='orange', width=4, dash='solid')
        ))

    # Vertical lines for away chances
    for (t, _), y in zip(away_chances, away_flag_ys):
        shapes.append(dict(
            type='line',
            x0=t, x1=t,
            y0=y, y1=0,
            line=dict(color='orange', width=2, dash='solid')
        ))

    home_flags = go.Scatter(
        x=[t for t, _ in home_chances],
        y=home_flag_ys,
        #y=[max(home_strength) + 0.5] * len(home_chances),
        mode='markers+text',
        marker=dict(size=40, color=flag_color, line=dict(width=5, color=home_team_color)),
        text=[c for _, c in home_chances],
        textposition='middle center',
        textfont=dict(size=30,color=text_color),
        showlegend=False
    )

    away_flags = go.Scatter(
        x=[t for t, _ in away_chances],
        y=away_flag_ys,
        #y=[-max(away_strength) - 0.5] * len(away_chances),
        mode='markers+text',
        marker=dict(size=41, color=flag_color, line=dict(width=5, color=away_team_color)),
        text=[c for _, c in away_chances],
        textposition='middle center',
        textfont=dict(size=30,color=text_color),
        showlegend=False
    )



    # # Vertical lines for home chances
    # for (t, _), y in zip(home_chances, home_flag_ys):
    #     shapes.append(dict(
    #         type='line',
    #         x0=t, x1=t,
    #         y0=0, y1=y,
    #         line=dict(color='orange', width=2, dash='solid')
    #     ))
    #
    # # Vertical lines for away chances
    # for (t, _), y in zip(away_chances, away_flag_ys):
    #     shapes.append(dict(
    #         type='line',
    #         x0=t, x1=t,
    #         y0=y, y1=0,
    #         line=dict(color='orange', width=2, dash='solid')
    #     ))

    layout = go.Layout(
        title='Average Time on Ice and Scoring Chances',
        xaxis=dict(title='Time (seconds)', range=[0, game_duration]),
        yaxis=dict(title='Average TOI for players on ice'),
        showlegend=True,
        height=1000,
        shapes=shapes
    )

    fig = go.Figure(data=[home_trace, away_trace, diff_trace, home_flags, away_flags], layout=layout)
    pyo.plot(fig, filename=filename, auto_open=False)

#def draw_shifts(game_id, roster=False):
def draw_shifts(shifts, player_data=None):
    # Load JSON data (replace with actual file path)
    # json_file_path = os.path.join(DATA_ROOT, f"IIHF_World_Championship/playsequences/{game_id}.json")

    # with open(json_file_path, "r") as file:
    #     data = json.load(file)
    #
    # if roster:
    #     player_map = get_roster(game_id)
    #     # with open(roster, "r") as file:
    #     #     roster = json.load(file)
    #     # teams = list(roster.keys())
    #     # player_info = [p for p in roster[teams[0]]['players']] + [p for p in roster[teams[1]]['players']]
    #     # player_map = {p['id']: p for p in player_info} #{"id": player_id} f"{p['firsts_name']} {p['last_name']} {p['position']}"
    #
    #
    # # Organize shifts by player
    # shifts = defaultdict(list)
    PERIOD_DURATION = 1200  # Each period is 1200 seconds

    # shifts = process_shifts(game_id)
    # player_map = get_roster(game_id)
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    players = list(shifts.keys())
    players.sort()  # Sort players for better visualization

    for i, player in enumerate(players):
        for shift in shifts[player]:
            if shift[1] is not None:
                ax.add_patch(mpatches.Rectangle((shift[0], i - 0.4), shift[1] - shift[0], 0.8, color="royalblue"))

    # Labels and formatting
    if player_data:
        labels = [f"{player_data[id]['first_name']} {player_data[id]['last_name']} {player_data[id]['position']}" for id in players]
    else:
        labels = [str(p) for p in players]

    ax.set_yticks(range(len(players)))
    ax.set_yticklabels(labels) #[f"Player {p}" for p in players])
    ax.set_xlabel("Gametime (s)")
    ax.set_title("Hockey Player Shifts")

    # Add period markers
    for period in range(1, 4):
        period_start = (period - 1) * PERIOD_DURATION
        ax.axvline(period_start, color="black", linestyle="--", alpha=0.7)
        ax.text(period_start + 50, len(players) + 1, f"Period {period}", fontsize=12, verticalalignment="bottom")

    ax.set_xlim(0, 3600)  # Full 60-minute game

    plt.show()
    input("Press Enter to exit...")  # Keeps window open



def process_shifts(game_id, league = 'SHL', include_goalies=False, team_id=None):
    """
    Convert raw JSON shift data into a structured format: {player_id: [(IN_time, OUT_time), ...]}
    Adjusts for period offsets (1200s per period).
    """
    file_path = os.path.join(DATA_ROOT, f"{league}/playsequences/shifts/{game_id}.json")
    with open(file_path, "r") as file:
        data = json.load(file)
    shifts = defaultdict(list)
    if not include_goalies:
        roster = get_roster(game_id)
        goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
        data = [d for d in data if d['player_id'] not in goalies]
    PERIOD_DURATION = 1200  # Each period is 1200 seconds

    if team_id:
        data = [d for d in data if d['team_id'] == str(team_id)]

    active_shifts = {}  # Tracks ongoing shifts (IN without OUT)

    for event in data:
        player_id = event["player_id"]
        period_offset = (event["period"] - 1) * PERIOD_DURATION
        event_time = event["period_time"] + period_offset

        if event["player_shift_event"] == "IN":
            active_shifts[player_id] = event_time  # Store IN event

        elif event["player_shift_event"] == "OUT":
            if player_id in active_shifts:
                shifts[player_id].append((active_shifts[player_id], event_time))  # Save shift
                del active_shifts[player_id]  # Remove from active shifts

    # Add still active shifts (players who never had an OUT event)
    for player_id, in_time in active_shifts.items():
        shifts[player_id].append((in_time, None))

    return shifts



def current_shift_time_on_ice(shifts, time_in_seconds):
    """
    Compute how long each player currently on the ice has been on the ice in their current shift.

    :param data: Raw JSON shift data
    :param time_in_seconds: The current game time in seconds.
    :return: Dictionary {player_id: time_on_ice}
    """
    # shifts = process_shifts(data)  # Convert raw data to structured format
    players_on_ice = {}

    for player_id, shift_list in shifts.items():
        for in_time, out_time in shift_list:
            if in_time <= time_in_seconds and (out_time is None or out_time > time_in_seconds):
                players_on_ice[player_id] = time_in_seconds - in_time
                break  # Only consider the most recent shift

    return players_on_ice

def get_team(sl_id):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    cursor.execute(f"select id, name from team where sl_id={sl_id};")
    res = cursor.fetchall()[0]
    return res

def get_roster(game_id, league='SHL'):
    roster = os.path.join(DATA_ROOT, f"{league}/playsequences/rosters/{game_id}.json")
    with open(roster, "r") as file:
        roster = json.load(file)
    teams = list(roster.keys())
    player_info = []

    p_1 = [p for p in roster[teams[0]]['players']]
    for p in p_1:
        p.update({"team":teams[0]})
    player_info = player_info + p_1

    p_2 = [p for p in roster[teams[1]]['players']]
    for p in p_2:
        p.update({"team":teams[1]})
    player_info = player_info + p_2

    player_map = {p['id']: p for p in
                  player_info}  # {"id": player_id} f"{p['firsts_name']} {p['last_name']} {p['position']}"

    return player_map
#def add_player_data(shifts, roster):

def shifts_reset_on_whistle(shifts, game_id=None, events=None):
    epsilon = 0.001
    if game_id:
        filename = os.path.join(DATA_ROOT, f"IIHF_World_Championship/playsequences/{game_id}.json")
        with open(filename, "r") as file:
            events = json.load(file)


    whistles = list(set([e['game_time'] for e in events['events'] if e['name'] == "whistle"]))
    whistles.sort()

    new_shifts = {}

    for key in shifts.keys():
        player_shifts = shifts[key]
        changes = True
        while changes:
            changes = False
            for whistle_time in whistles:
                for player_shift in player_shifts:
                    if player_shift[0] < (whistle_time - epsilon) and (whistle_time + epsilon) < player_shift[1]:
                        changes = True
                        #print(player_shift)
                        #print(whistle_time)
                        player_shifts.remove(player_shift)
                        player_shifts.append((player_shift[0], whistle_time))
                        player_shifts.append((whistle_time, player_shift[1]))


        new_shifts[key] = player_shifts


    return new_shifts

def get_teams(game_id):
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()

    sql = f"select sl_homeTeamId, sl_awayTeamId from game where sl_id={game_id};"
    cursor.execute(sql)
    return cursor.fetchall()[0]

def fatigued_corsi_team():
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    games = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/all_games_213.json", "r"))['games']
    res = {}
    ctr=0
    for game in games:
        ctr += 1

        season=game['seasonId']
        teams = get_teams(game["id"])
        print(ctr, " ", season, " ", teams)
        #game_details = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/{game['id']}.json", "r"))
        game_details = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/with_suevents_wo_gameevents/{game['id']}.json", "r"))

        df = pd.DataFrame.from_records(game_details['events'])
        all_shots = df[df['name']=='shot']
        all_shots = all_shots[all_shots['skatersOnIceSituation'] == "5v5"]
        home_team_for = all_shots[all_shots['teamId'] == str(teams[0])]['gameTime']
        away_team_for = all_shots[all_shots['teamId'] == str(teams[1])]['gameTime']
        shifts_home_team = process_shifts(game['id'], team_id=teams[0])
        shifts_away_team = process_shifts(game['id'], team_id=teams[1])

        #team = teams[0]
        for team in teams:
            if f"{team}_{season}" not in res.keys():
                new_key = f"{team}_{season}"
                res.update({new_key:{"sf":[], "sa":[]}})
                print("new key generated: ", new_key)
        toi_ht_for = [current_shift_time_on_ice(shifts_home_team, t) for t in list(home_team_for)]
        toi_avr_ht_for = [sum(p.values()) / len(p.values()) for p in toi_ht_for if len(p.values()) > 2]

        toi_ht_against = [current_shift_time_on_ice(shifts_home_team, t) for t in list(away_team_for)]
        toi_avr_ht_against = [sum(p.values()) / len(p.values()) for p in toi_ht_against if len(p.values()) > 2]

        toi_at_for = [current_shift_time_on_ice(shifts_away_team, t) for t in list(away_team_for)]
        toi_avr_at_for = [sum(p.values()) / len(p.values()) for p in toi_at_for if len(p.values()) > 2]

        toi_at_against = [current_shift_time_on_ice(shifts_away_team, t) for t in list(home_team_for)]
        toi_avr_at_against = [sum(p.values()) / len(p.values()) for p in toi_at_against if len(p.values()) > 2]

        res[f"{teams[0]}_{season}"]['sf'] += toi_avr_ht_for
        res[f"{teams[0]}_{season}"]['sa'] += toi_avr_ht_against
        res[f"{teams[1]}_{season}"]['sf'] += toi_avr_at_for
        res[f"{teams[1]}_{season}"]['sa'] += toi_avr_at_against


        #print(res.keys())
    with open("kalle.json", "w") as f:
        json.dump(res, f, indent=4)

def format_corsi_team(data):

    formatted = []
    for item in data:
        team_name = get_team(item['team'])
        item['team_name'] = team_name[1]
        formatted.append(item.copy())
    return formatted



def corsi_shift_time(data, threshold, season = None):

    if season:
        keys = data.keys()
        season_keys = [k for k in list(keys) if k.split('_')[1] == str(season)]
        keys = season_keys
    else:
        keys = data.keys()
    teams = [k.split('_')[0] for k in keys]
    teams = list(set(teams))
    res = []
    for team in teams:
        sf = []
        sa = []
        for entry in [p for p in list(keys) if team in p]:
            sf += data[entry]['sf']
            sa += data[entry]['sa']

        sf_tired = len([f for f in sf if f > threshold])
        sf_fresh = len([f for f in sf if f <= threshold])
        sa_tired = len([f for f in sa if f > threshold])
        sa_fresh = len([f for f in sa if f <= threshold])

        new_item = {}
        new_item['team'] = team

        new_item['corsi_fresh'] = float(sf_fresh) / (float(sf_fresh + sa_fresh)) if sf_fresh+sa_fresh > 5 else -1
        new_item['corsi_tired'] = float(sf_tired) / (float(sf_tired + sa_tired)) if sf_tired+sa_tired > 5 else -1
        res.append(new_item.copy())

    # for r in res:
    #     print(f"{r['team']}: {r['corsi_fresh']} {r['corsi_tired']}")

    return res

if __name__ == '__main__':

    #### Create frame_time_maps #####################################
    b=os.listdir("/home/veronica/hockeystats/ver2/SHL/playsequences")
    base_dir = "/home/veronica/hockeystats/ver2/SHL/playsequences"
    game_ids = [int(os.path.splitext(k)[0]) for k in b if os.path.splitext(k)[0].isnumeric()]
    # j = json.load(open(f"/home/veronica/hockeystats/ver2/SHL/all_games_13.json", "r"))
    # game_ids = [k['id'] for k in j['games'] if k['seasonId'] == '11']
    # #for game_id in game_ids:
    # #    apiv2.create_frame_to_time(game_id, base_dir)
    # #exit(0)
    ######################################################################

    s = process_shifts(game_ids[0])
    game_id = 137440
    #data = json.load(open("kalle.json","r"))
    data = json.load(open("corsi_shifts.json","r"))

    for season in list(data.keys()):
        print("\n\n---------------------------------------------")
        print(f"{season}\n")
        print("---------------------------------------------\n\n")
        for item in data[season]:
            #df=pd.DataFrame.from_records([item])['team_name']
            #print(df)
            #df = item[['team_name', 'corsi_fresh', 'corsi_tired']]
            print(f"{item['team_name']} \t\t {100*round(item['corsi_fresh'],2):.1f} \t   {100*round(item['corsi_tired'],2):.1f}")
    exit(0)
    all_res = {}
    for season in [7,8,9,10]:
        res = corsi_shift_time(data,45, season=season)
        res = format_corsi_team(res)
        all_res[str(2021 + season - 7)] = res
    res = corsi_shift_time(data, 45)
    res = format_corsi_team(res)
    all_res['total'] = res
    with open('corsi_shifts','w') as f:
        json.dump(all_res, f)
    #fatigued_corsi_team()
    exit(0)
    # ingest.ingest_events(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/{game_id}.json")
    game = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/{game_id}.json", "r"))
    df = pd.DataFrame.from_records(game['events'])


    shifts = process_shifts(game_id, team_id=1335)
    shifts = shifts_reset_on_whistle(shifts, game_id)
    player_data = get_roster(game_id)

    toi = [current_shift_time_on_ice(shifts,float(t)) for t in list(range(0,3600))]
    toi = [sum(p.values())/len(p.values()) for p in toi]
    draw_shifts(shifts, player_data = player_data)



import numpy as np



def oz_histogram(oz_entries, intervals=3, ax=None):
    # Filter valid entries and group by type
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))  # fallback for standalone use
    else:
        fig = ax.figure
    types = ['carry', 'dumpin', 'pass']
    type_times = {t: [] for t in types}

    for entry in oz_entries:
        t = entry.get('entry_type')
        time = entry.get('time_to_first_shot')
        if t in type_times and time is not None:
            type_times[t].append(time)

    # Check if there's any data
    if not any(type_times[t] for t in types):
        raise ValueError("No valid 'time_to_first_shot' data available.")

    # Define bins based on combined data
    all_times = [time for times in type_times.values() for time in times]
    max_time = max(all_times)
    bins = np.arange(0, max_time + intervals, intervals)

    # Stack the histogram
    #plt.figure(figsize=(10, 6))
    ax.hist(
        [type_times[t] for t in types],
        bins=bins,
        stacked=True,
        label=types,
        edgecolor='black'
    )

    # Set x-axis labels
    bin_labels = [f"({int(bins[i])}-{int(bins[i + 1])})" for i in range(len(bins) - 1)]
    ax.set_xticks(bins[:-1] + intervals / 2, bin_labels, rotation=45)

    ax.set_xticklabels(bin_labels, rotation=45)
    ax.set_ylabel('Frequency')
    #ax.set_title('Histogram of Time to First Shot by Entry Type')
    ax.legend(title="Entry Type")
    #ax.tight_layout()
    return ax




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
    plt.sca(ax)
    plt.show()
    return ax

import matplotlib.pyplot as plt
import io
import base64

def piechart_ozentries(oz_entries, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))  # fallback for standalone use
    else:
        fig = ax.figure
    types = ['carry', 'dumpin', 'pass']
    total_counts = {t: 0 for t in types}
    shot_counts = {t: 0 for t in types}

    for entry in oz_entries:
        t = entry.get('entry_type')
        if t in types:
            total_counts[t] += 1
            if entry.get('time_to_first_shot') is not None:
                shot_counts[t] += 1

    # Prepare data for pie chart
    labels = []
    sizes = []
    for t in types:
        total = total_counts[t]
        shots = shot_counts[t]
        if total > 0:
            labels.append(f"{t.capitalize()} ({shots}/{total} entries with shot)")
            sizes.append(total)

    if not sizes:
        raise ValueError("No valid OZ entries available.")

    # Plot pie chart
    #plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.0f%%', startangle=140
    )
    for autotext in autotexts:
        autotext.set_fontsize(14)
    #ax.set_title('OZ Entries')
    #ax.tight_layout()

    return ax
