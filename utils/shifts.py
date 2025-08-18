import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import db_tools
from utils.file_tools import get_filepath
from utils.data_tools import add_team_id_to_game_info
import dotenv
import os
import ingest
import pandas as pd
import numpy as np
from utils.data_tools import scoring_chances
import visualizations
# import entries
#from generate_entry_statistics import stats_db
import apiv2

dotenv.load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT")
import db_tools
from utils import file_tools

def scoring_chances_vs_shifts_lengths(game_id=None, game_data=None, filename=None):
    if filename is None:
        filename = f"scoring_chances_vs_shifts_lengths_{game_id}.html"

    if game_data is None:
        game_data = file_tools.get_game_dicts(game_id, ignore = 'playsequence_compiled')

    all_scoring_chances = scoring_chances(game_data) #playsequence, game_info)
    scoring_chances_home_team = all_scoring_chances['home_team']
    scoring_chances_away_team = all_scoring_chances['away_team']
    toi_home_team, toi_away_team = shift_data(game_data) #game_id)

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
    visualizations.create_interactive_line_plot(toi_home_team, toi_away_team, scoring_chances_home_team, scoring_chances_away_team, filename=filename)

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


def shift_data(game_data, game_id=None):
    playsequence = game_data['playsequence']
    game_info = game_data['game-info']
    shifts = game_data['shifts']
    roster = game_data['roster']
    roster = get_roster_from_dict(roster)

    game_end_time = int(np.ceil(playsequence['events'][-1]['game_time']))

    goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
    shift_data = [s for s in shifts if s['player_id'] not in goalies]
    home_team_id = game_info['home_team']['id']
    away_team_id = game_info['away_team']['id']
    data_home_team = process_shifts(shift_data,team_id=home_team_id)
    data_away_team = process_shifts(shift_data, team_id=away_team_id)
    data_home_team = shifts_reset_on_whistle(data_home_team, playsequence)
    data_away_team = shifts_reset_on_whistle(data_away_team, playsequence)
    toi_home_team = [current_shift_time_on_ice(data_home_team, p) for p in range(0,game_end_time)]
    toi_away_team = [current_shift_time_on_ice(data_away_team, p) for p in range(0, game_end_time)]
    return toi_home_team, toi_away_team

def process_shifts(data, team_id=None): #, league = 'SHL', include_goalies=False, team_id=None):
    """
    Convert raw JSON shift data into a structured format: {player_id: [(IN_time, OUT_time), ...]}
    Adjusts for period offsets (1200s per period).
    """
    # file_path = os.path.join(DATA_ROOT, f"{league}/shifts/{game_id}.json")
    # with open(file_path, "r") as file:
    #     data = json.load(file)
    # shifts = defaultdict(list)
    # if not include_goalies:
    #     roster = get_roster(game_id, league=league)
    #     goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
    #     data = [d for d in data if d['player_id'] not in goalies]
    PERIOD_DURATION = 1200  # Each period is 1200 seconds

    if team_id:
        data = [d for d in data if d['team_id'] == str(team_id)]

    active_shifts = {}  # Tracks ongoing shifts (IN without OUT)

    shifts = defaultdict(list)
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
    roster = os.path.join(DATA_ROOT, f"{league}/rosters/{game_id}.json")
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

def get_roster_from_dict(roster):

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

def shifts_reset_on_whistle(shifts, playsequence): #sl_game_id=None, league_name='SHL', events=None):
    epsilon = 0.001
    # if sl_game_id:
    #     filename = os.path.join(DATA_ROOT, f"{league_name}/playsequences/{sl_game_id}.json")
    #     with open(filename, "r") as file:
    #         events = json.load(file)


    whistles = list(set([e['game_time'] for e in playsequence['events'] if e['name'] == "whistle"]))
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


        print(res.keys())
    with open("../kalle.json", "w") as f:
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

    for r in res:
        print(f"{r['team']}: {r['corsi_fresh']} {r['corsi_tired']}")

    return res