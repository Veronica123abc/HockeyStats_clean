import json
import dotenv
import os

from utils import file_tools #team_ids_from_name
# import entries
#from generate_entry_statistics import stats_db
from utils import shifts as sh, file_tools
import db_tools
import pandas as pd


def shots_es(df):
    all_shots = df[df['name'] == 'shot']
    all_shots = all_shots[all_shots['manpowersituation'] == "evenStrength"]
    return all_shots

def goals_es(df):
    all_shots = df[df['shorthand'] == 'GOAL']
    all_shots = all_shots[all_shots['manpowersituation'] == "evenStrength"]
    return all_shots

def fatigued_corsi_team():
    stats_db = db_tools.open_database("hockeystats_ver2")
    cursor = stats_db.cursor()
    games = json.load(open(f"/home/veronica/hockeystats/ver2/SHL/all_games_13.json", "r"))['games']
    games = [g for g in games if g['seasonId'] == '11']
    res = {}
    ctr=0
    for game in games[1:]:
        ctr += 1

        season=game['seasonId']

        teams = db_tools.get_teams(game["id"])
        print(ctr, " ", season, " ", teams)
        #game_details = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/{game['id']}.json", "r"))
        #game_details = json.load(open(f"/home/veronica/hockeystats/ver2/IIHF_World_Championship/playsequences/with_suevents_wo_gameevents/{game['id']}.json", "r"))
        game_details = json.load(open(f"/home/veronica/hockeystats/ver2/SHL/playsequences_compiled/{game['id']}.json","r"))
        #team_map = file_tools.team_ids_from_name(game_details)
        df = pd.DataFrame.from_records(game_details['events'])
        #team_in_possession = df.team_in_possession
        #tip = team_in_possession.dropna().apply(lambda t: team_map.get(t))
        #df['team_in_possession'] = tip
        #selection = df[df['name']=='shot']
        #selection = selection[selection['manpowersituation'] == "evenStrength"]
        selection = goals_es(df)
        home_team_for = selection[selection['team_id'] == str(teams[0])]['game_time']
        away_team_for = selection[selection['team_id'] == str(teams[1])]['game_time']
        shifts_home_team = sh.process_shifts(game['id'], team_id=teams[0])
        shifts_home_team = sh.shifts_reset_on_whistle(shifts_home_team, game['id'])
        shifts_away_team = sh.process_shifts(game['id'], team_id=teams[1])
        shifts_away_team = sh.shifts_reset_on_whistle(shifts_away_team, game['id'])

        #team = teams[0]
        for team in teams:
            if f"{team}_{season}" not in res.keys():
                new_key = f"{team}_{season}"
                res.update({new_key:{"sf":[], "sa":[]}})
                print("new key generated: ", new_key)
        toi_ht_for = [sh.current_shift_time_on_ice(shifts_home_team, t) for t in list(home_team_for)]
        toi_avr_ht_for = [sum(p.values()) / len(p.values()) for p in toi_ht_for if len(p.values()) > 2]

        toi_ht_against = [sh.current_shift_time_on_ice(shifts_home_team, t) for t in list(away_team_for)]
        toi_avr_ht_against = [sum(p.values()) / len(p.values()) for p in toi_ht_against if len(p.values()) > 2]

        toi_at_for = [sh.current_shift_time_on_ice(shifts_away_team, t) for t in list(away_team_for)]
        toi_avr_at_for = [sum(p.values()) / len(p.values()) for p in toi_at_for if len(p.values()) > 2]

        toi_at_against = [sh.current_shift_time_on_ice(shifts_away_team, t) for t in list(home_team_for)]
        toi_avr_at_against = [sum(p.values()) / len(p.values()) for p in toi_at_against if len(p.values()) > 2]

        res[f"{teams[0]}_{season}"]['sf'] += toi_avr_ht_for
        res[f"{teams[0]}_{season}"]['sa'] += toi_avr_ht_against
        res[f"{teams[1]}_{season}"]['sf'] += toi_avr_at_for
        res[f"{teams[1]}_{season}"]['sa'] += toi_avr_at_against


        print(res.keys())
    with open("shl_goal.json", "w") as f:
        json.dump(res, f, indent=4)
    return res


def format_corsi_team(data):

    formatted = []
    for item in data:
        team_name = db_tools.get_team(item['team'])
        item['team_name'] = team_name[1]
        formatted.append(item.copy())
    return formatted



def corsi_shift_time_ratio(data, threshold, season = None):

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
        new_item['team_name'] = db_tools.get_team(team)
        res.append(new_item.copy())

    for r in res:
        print(f"{r['team_name']}: {r['corsi_fresh']} {r['corsi_tired']}")

    return res

def corsi_shift_time_numbers(data, threshold, season = None):

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
        new_item['corsi_for_fresh'] = sf_fresh
        new_item['corsi_against_fresh'] = sa_fresh
        new_item['corsi_for_tired'] = sf_tired
        new_item['corsi_against_tired'] = sa_tired
        new_item['team_name'] = db_tools.get_team(team)
        res.append(new_item.copy())

    for r in res:
        print(f"{r['team_name']}: {r['corsi_for_fresh']} {r['corsi_against_fresh']}             {r['corsi_for_tired']} {r['corsi_against_tired']}")

    return res



dotenv.load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT")
if __name__ == '__main__':
    #exit(0)
    #fatigued_corsi_team()
    #exit(0)
    j = json.load(open(f"shl_goal.json", "r"))
    #corsi_shift_time_ratio(j,45)
    corsi_shift_time_numbers(j,45)
    exit(0)
    j = json.load(open(f"/home/veronica/hockeystats/ver2/SHL/all_games_13.json", "r"))
    game_ids = [k['id'] for k in j['games'] if k['seasonId']=='11']
    game_id = game_ids[0]
    shifts = sh.process_shifts(game_id)
    shifts = sh.shifts_reset_on_whistle(shifts, league_name='SHL', sl_game_id=game_id)
    player_data = file_tools.get_roster(game_id)
    # toi = current_shift_time_on_ice(shifts, 254.2)
    #toi = [sh.current_shift_time_on_ice(shifts, float(t)) for t in list(range(0, 3600))]
    #toi = [sum(p.values()) / len(p.values()) for p in toi]
    #sh.draw_shifts(shifts, player_data=player_data)
    print("apa")