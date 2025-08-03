import db_tools
import os
import entries
import numpy as np
import cv2
import sendmail
import os
import visualizations
from utils import read_write
import json
import pandas as pd
from ingest import get_map
import apiv2
nan = np.nan
from utils import shifts as sh, file_tools
import data_collection
import plotly.graph_objs as go
import plotly.offline as pyo
from difflib import SequenceMatcher
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import matplotlib.gridspec as gridspec
def get_filepath(game_id):
    return f"/home/veronica/hockeystats/ver3/{game_id}"

def downsample(data, bin_size):
    """
    Downsamples the data by taking mean over bins of size `bin_size`.
    """
    n_bins = len(data) // bin_size
    data = data[:n_bins * bin_size]  # Trim excess
    return np.mean(data.reshape(-1, bin_size), axis=1)

def interpolate_strength(waypoints):
    length = len(waypoints)
    """
    Interpolates a list of (time, value) tuples over `length` seconds.
    """
    times, values = zip(*waypoints)
    full_time = np.arange(length)
    interpolated = np.interp(full_time, times, values)
    return interpolated

def create_interactive_line_plot(home_wp, away_wp, home_chances, away_chances, filename='hockey_visual3.html'):
    home_strength = interpolate_strength(home_wp)
    away_strength = interpolate_strength(away_wp)
    game_duration = len(home_wp)
    x = np.arange(game_duration)

    home_y_offsets = [0.5, 0.9, 1.3]
    away_y_offsets = [0.5, 0.9, 1.3]
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

def plot_hockey_game_visual(
    hometeam_strength_wp,
    awayteam_strength_wp,
    hometeam_chances,
    awayteam_chances,
    bin_size=30
):
    # Interpolate strength values
    game_duration = len(hometeam_strength_wp)
    hometeam_strength = interpolate_strength(hometeam_strength_wp)
    awayteam_strength = interpolate_strength(awayteam_strength_wp)

    # Downsample
    home_bars = downsample(hometeam_strength, bin_size)
    away_bars = downsample(awayteam_strength, bin_size)

    #x = np.arange(0, len(home_bars) * bin_size, bin_size)
    x = np.arange(len(hometeam_strength))

    plt.figure(figsize=(14, 6))

    # Plot strengths

    #plt.plot(x, hometeam_strength, color='red', label='Home Team Average TOI',linewidth=2)
    #plt.plot(x, -awayteam_strength, color='blue', label='Away Team Average TOI', linewidth=2)
    plt.plot(x, hometeam_strength - awayteam_strength, color='green', label='Difference TOI', linewidth=4)

    # Plot home team chances
    for t, c in hometeam_chances:
        plt.text(t, max(hometeam_strength) + 0.5, c, ha='center', va='bottom',
                 fontsize=12, bbox=dict(boxstyle='circle', facecolor='white', edgecolor='black'))

    # Plot away team chances
    for t, c in awayteam_chances:
        plt.text(t, -max(awayteam_strength) - 0.5, c, ha='center', va='top',
                 fontsize=12, bbox=dict(boxstyle='circle', facecolor='white', edgecolor='black'))

    plt.axhline(0, color='gray', linewidth=1)
    plt.xlim(0, game_duration)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Team Strength')
    plt.title('Hockey Game Strength & Goal Scoring Opportunities')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def add_team_id_to_game_info(playsequence, roster, game_info):
    teams = list(set([a['team_in_possession'] for a in playsequence['events'] if (a['team_in_possession'] is not None) and (not a['team_in_possession'] == 'None')]))
    print(teams)
    player_id = [p['team_forwards_on_ice_refs'] for p in playsequence['events'] if p['team_in_possession'] == teams[0]][0][0]
    player_team = roster[player_id]['team']
    if game_info['home_team']['id'] == player_team:
        game_info['ps_home_team_name'] = teams[0]
        game_info['ps_away_team_name'] = teams[1]
    else:
        game_info['ps_home_team_name'] = teams[1]
        game_info['ps_away_team_name'] = teams[0]

    return game_info

def shots_es(game_details):
    df = pd.DataFrame.from_records(game_details['events'])
    all_shots = df[df['name'] == 'shot']
    all_shots = all_shots[all_shots['manpowersituation'] == "evenStrength"]


def shift_data(game_id):
    with open(get_filepath(game_id) + "/game-info.json") as f:
        game_info = json.load(f)
    with open(get_filepath(game_id) + "/shifts.json") as f:
        data = json.load(f)
    # Remove goalies
    with open(get_filepath(game_id) + "/roster.json") as f:
        roster = json.load(f)
        roster = sh.get_roster_from_dict(roster)
    with open(get_filepath(game_id) + "/playsequence.json") as f:
        playsequence = json.load(f)
    with open(get_filepath(game_id) + "/playsequence_compiled.json") as f:
        playsequence_compiled = json.load(f)
    game_end_time = int(np.ceil(playsequence['events'][-1]['game_time']))
    teams = list(set([a['team_in_possession'] for a in playsequence['events'] if (a['team_in_possession'] is not None) and (not a['team_in_possession'] == 'None')]))
    print(teams)

    game_info = add_team_id_to_game_info(playsequence, roster, game_info)

    goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
    data = [d for d in data if d['player_id'] not in goalies]
    home_team_id = game_info['home_team']['id']
    away_team_id = game_info['away_team']['id']
    data_home_team = sh.process_shifts(data,team_id=home_team_id)
    data_away_team = sh.process_shifts(data, team_id=away_team_id)
    data_home_team = sh.shifts_reset_on_whistle(data_home_team, playsequence)
    data_away_team = sh.shifts_reset_on_whistle(data_away_team, playsequence)
    toi_home_team = [sh.current_shift_time_on_ice(data_home_team, p) for p in range(0,game_end_time)]
    toi_away_team = [sh.current_shift_time_on_ice(data_away_team, p) for p in range(0, game_end_time)]
    return toi_home_team, toi_away_team

def corsi_fatigued(game_id):
    game_info, data, roster, playsequence = get_all_game_data(game_id)

    toi_home_team, toi_away_team = shift_data(game_id)



def get_all_game_data(game_id):
    with open(get_filepath(game_id) + "/game-info.json") as f:
        game_info = json.load(f)
    with open(get_filepath(game_id) + "/shifts.json") as f:
        data = json.load(f)
    # Remove goalies
    with open(get_filepath(game_id) + "/roster.json") as f:
        roster = json.load(f)
        roster = sh.get_roster_from_dict(roster)
    with open(get_filepath(game_id) + "/playsequence.json") as f:
        playsequence = json.load(f)

    return game_info, data, roster, playsequence



def shifts(game_id):
    with open(get_filepath(game_id) + "/game-info.json") as f:
        game_info = json.load(f)
    with open(get_filepath(game_id) + "/shifts.json") as f:
        data = json.load(f)
    # Remove goalies
    with open(get_filepath(game_id) + "/roster.json") as f:
        roster = json.load(f)
        roster = sh.get_roster_from_dict(roster)
    with open(get_filepath(game_id) + "/playsequence.json") as f:
        playsequence = json.load(f)
    # with open(get_filepath(game_id) + "/playsequence_compiled.json") as f:
    #     playsequence_compiled = json.load(f)
    # game_end_time = int(np.ceil(playsequence['events'][-1]['game_time']))
    teams = list(set([a['team_in_possession'] for a in playsequence['events'] if (a['team_in_possession'] is not None) and (not a['team_in_possession'] == 'None')]))
    print(teams)
    player_id = [p['team_forwards_on_ice_refs'] for p in playsequence['events'] if p['team_in_possession'] == teams[0]][0][0]
    player_team = roster[player_id]['team']
    if game_info['home_team']['id'] == player_team:
        game_info['ps_home_team_name'] = teams[0]
        game_info['ps_away_team_name'] = teams[1]
    else:
        game_info['ps_home_team_name'] = teams[1]
        game_info['ps_away_team_name'] = teams[0]


    goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
    a_chances_home_team = [(p['game_time'], 'A') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'A' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_home_team_name']]
    a_chances_away_team = [(p['game_time'], 'A') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'A' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_away_team_name']]
    b_chances_home_team = [(p['game_time'], 'B') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'B' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_home_team_name']]
    b_chances_away_team = [(p['game_time'], 'B') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'B' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_away_team_name']]
    c_chances_home_team = [(p['game_time'], 'C') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'C' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_home_team_name']]
    c_chances_away_team = [(p['game_time'], 'C') for p in playsequence['events'] if p['expected_goals_all_shots_grade'] == 'C' and
                           p['team_skaters_on_ice']==5 and
                           p['opposing_team_skaters_on_ice'] == 5 and
                           p['team_in_possession'] == game_info['ps_away_team_name']]

    scoring_chances_home_team = a_chances_home_team + b_chances_home_team + c_chances_home_team
    scoring_chances_away_team = a_chances_away_team + b_chances_away_team + c_chances_away_team
    toi_home_team, toi_away_team = shift_data(game_id)

    # Hack to avoid None
    res = [toi_home_team[0]]
    for p in toi_home_team[1:]:
        if len(p.values()) == 0:
            res.append(res[-1])
        else:
            res.append(p)
    toi_home_team = res
    res = [toi_away_team[0]]
    for p in toi_away_team[1:]:
        if len(p.values()) == 0:
            res.append(res[-1])
        else:
            res.append(p)
    toi_away_team = res
    ####################################
    toi_home_team = [int(np.mean(list(p.values()))) for p in toi_home_team if len(list(p.values())) > 0 ]
    toi_away_team = [int(np.mean(list(p.values()))) for p in toi_away_team if len(list(p.values())) > 0]
    toi_home_team = [(a, b) for a,b in zip(range(0,len(toi_home_team)), toi_home_team)]
    toi_away_team = [(a, b) for a, b in zip(range(0, len(toi_away_team)), toi_away_team)]
    create_interactive_line_plot(toi_home_team, toi_away_team, scoring_chances_home_team, scoring_chances_away_team)
    #plot_hockey_game_visual(toi_home_team, toi_away_team, scoring_chances_home_team, scoring_chances_away_team)

    # toi_home_team_A = [sh.current_shift_time_on_ice(data_home_team, int(p)) for p in a_chances_home_team]
    # toi_away_team_A = [sh.current_shift_time_on_ice(data_away_team, int(p)) for p in a_chances_home_team]
    # total_home_team_A = [sum(list(a.values())) for a in toi_home_team_A]
    # total_away_team_A = [sum(list(a.values())) for a in toi_away_team_A]
    # for idx, (a,b) in enumerate(zip(total_home_team_A, total_away_team_A)):
    #     print (a-b)
    #
    #
    #
    # print("apa")


def oz_stats(game_id):
    # req = requests.Session()
    #apiurl = "https://api.sportlogiq.com"
    #req = apiv2.login()
    #games = json.load(open("/home/veronica/hockeystats/ver2/5_Nations_Tournament_U17/games_2025.json", "r"))
    #game_ids = [int(game['id']) for game in games['games'] if games['seasonId'] == '10']


    filepath = get_filepath(game_id) + "/playsequence_compiled.json"
    if not os.path.exists(filepath):
        return None
    with open(filepath,"r") as f:
        events = json.load(f)

    if len(events['events']) > 0:
        c_map = get_map()
        df = pd.DataFrame.from_dict(events['events'])
        df = df.rename(columns=c_map[0])
        oz_rallies = entries.get_oz_rallies(df)
        teams = [t for t in list(oz_rallies.keys()) if t is not None]
        tts_t1 = entries.time_entry_to_shots(oz_rallies[teams[0]])
        tts_t2 = entries.time_entry_to_shots(oz_rallies[teams[1]])

        tts_t1 = [e['rally_stat'] for e in tts_t1]
        tts_t2 = [e['rally_stat'] for e in tts_t2]

        #k = visualizations.entry_histogram(tts_t1)
        # Create side-by-side axes
        #fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        #fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        #(ax1, ax2), (ax3, ax4) = axs

        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1], hspace=0.5)  # <- adjust hspace here

        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 0])
        ax4 = fig.add_subplot(gs[1, 1])


        # Draw both plots
        visualizations.oz_histogram(tts_t1, ax=ax1)
        visualizations.piechart_ozentries(tts_t1, ax=ax2)
        visualizations.oz_histogram(tts_t2, ax=ax3)
        visualizations.piechart_ozentries(tts_t2, ax=ax4)
        fig.text(0.5, 0.92, f"{teams[0]}", ha='center', fontsize=20, weight='bold')
        fig.text(0.5, 0.46, f"{teams[1]}", ha='center', fontsize=20, weight='bold')
        #fig.tight_layout()
        fig.tight_layout(rect=[0, 0, 1, 0.9])
        fig.savefig("apa.png")
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        #img = cv2.imdecode(np.frombuffer(buf.read(), np.uint8), cv2.IMREAD_COLOR)
        #cv2.imshow("apa", img)
        #cv2.waitKey(0)

        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Histogram</title></head>
        <body><img src="data:image/png;base64,{img_base64}" /></body>
        </html>
        """
        #piechart = visualizations.piechart_ozentries(tts_t1)
        #histogram = visualizations.oz_histogram(tts_t1)
        with open(f"{game_id}.html","w") as f:
            f.write(html_content)



def download_test():
    files = os.listdir("/home/veronica/hockeystats/ver2/IIHF_World_Championship/gamefiles")
    files = [os.path.splitext(f)[0] for f in files]
    for f in files[1:5]:
        #data_collection.download_complete_game(int(f), playsequence=False, playsequence_compiled=False, roster=False, shifts=False)
        data_collection.download_complete_game(int(f))

if __name__ == "__main__":
    #download_test()
    # files = os.listdir("/home/veronica/hockeystats/ver2/IIHF_World_Championship/gamefiles")
    # files = [os.path.splitext(f)[0] for f in files]
    # for f in files[1:5]:
    #data_collection.download_complete_game(168745)
    # oz_stats(168745)
    #shifts(168742)
    sd = sh.shift_data(168742)
    print(sd)




# for team_id, team_name in teams:
#     sql = f"select id from game where (home_team_id={team_id} or away_team_id={team_id}) and date > \'2024-07-01\' and date < \'2025-01-11\';"
#     cursor.execute(sql)
#     games = cursor.fetchall()
#     print(len(games))
#     game_ids = [g[0] for g in games]
#     #cursor.execute("select team.id from team join participation on team.id=participation.team_id where participation.league_id=4 and season ='2024-25';")
#     #teams = cursor.fetchall()
#
#
#
#     game_statistics = []
#     #game_ids = [5963]
#     oz_rallies = []
#     for idx, game_id in enumerate(game_ids):
#         teams = db_tools.teams_in_game(game_id)
#         df = db_tools.get_events_from_game_with_team(game_id)
#         if len(df) == 0:
#             print("Empty")
#         else:
#             a,b,c,d = entries.puck_zone(df, team_id=teams['home_team_id']) #, teams=[75,73])
#             num_long_oz = len([r[5] for r in a if r[5] > 40])
#             oz_rallies.append(num_long_oz)
#             print(team_name, ' ', oz_rallies)
#
#     with open(f"/home/veronica/repos/HockeyStats_clean/tmp/{team_name}.txt",'w') as file:
#         res = " ".join([str(r) for r in oz_rallies])
#         res = team_name + ' ' + res
#         file.write(res)
#         file.close()