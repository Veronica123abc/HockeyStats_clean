import json
import dotenv
import os
import time
from utils import file_tools #team_ids_from_name
# import entries
#from generate_entry_statistics import stats_db
import matplotlib.pyplot as plt

import db_tools
import pandas as pd
from tqdm import tqdm
from utils.shifts import shift_data, process_shifts, shifts_reset_on_whistle, current_shift_time_on_ice
from utils.data_tools import add_team_id_to_game_info
from utils import data_tools
import numpy as np

def player_shift_average(shifts):
    res = []
    shifts=shifts['all_shifts']
    players = list(set([k['player_id'] for k in shifts]))
    ctr = 0
    for player in players:
        ctr += 1
        print(f"Computing data for player {player} ({ctr} of {len(players)})")
        player_shift_lengths = [k['player_shifts'] for k in shifts if k['player_id'] == player]
        all_player_shift_lengths = sum(player_shift_lengths,[])
        res.append(
            {
                'player_id': player,
                'n': len(all_player_shift_lengths),
                'mean': np.mean(all_player_shift_lengths),
                'std': np.std(all_player_shift_lengths)
            }
        )
    res_dict = {
        'player_season':res
    }
    return res_dict


def aggregated_average_shift_lengths(games):
    flat_res = []
    ctr = 0
    res = {}
    for game in games:
        ctr += 1
        print(f"Game {game} ({ctr} of {len(games)})")

        game_data = file_tools.get_game_dicts(game, ignore='playsequence_compiled')
        game_info = game_data['game-info']
        shift_info = game_data['shifts']
        roster = game_data['roster']
        roster = file_tools.player_based_roster(roster)
        playsequence = game_data['playsequence']

        #game_info, shift_info, roster, playsequence, playsequence_compiled = file_tools.get_game_dicts(game)
        game_info = add_team_id_to_game_info(playsequence, roster, game_info)
        goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
        data = [d for d in shift_info if d['player_id'] not in goalies]
        home_team_id = game_info['home_team']['id']
        away_team_id = game_info['away_team']['id']

        data_home_team = process_shifts(data, team_id=home_team_id)
        data_away_team = process_shifts(data, team_id=away_team_id)

        data_home_team = shifts_reset_on_whistle(data_home_team, playsequence)
        data_away_team = shifts_reset_on_whistle(data_away_team, playsequence)

        for player in data_home_team.keys():
            if player not in res.keys():
                res[player] = []
            player_shift_lengths = [k[1] - k[0] for k in data_home_team[player]]
            flat_res.append(
                {

                    'game_id': game_info['id'],
                    'team_id': home_team_id,
                    'player_id': player,
                    'player_shifts': player_shift_lengths,
                    'n': len(player_shift_lengths),
                    'avg': np.mean(player_shift_lengths),
                    'std': np.std(player_shift_lengths)
                }
            )
        for player in data_away_team.keys():
            if player not in res.keys():
                res[player] = []
            player_shift_lengths = [k[1] - k[0] for k in data_away_team[player]]
            flat_res.append(
                {
                    'player_id': player,
                    'game_id': game_info['id'],
                    'team_id': home_team_id,
                    'player_shifts': player_shift_lengths,
                    'n': len(player_shift_lengths),
                    'avg': np.mean(player_shift_lengths),
                    'std': np.std(player_shift_lengths)
                }
            )

    return flat_res

# def average_shift_length_all_players(season, league=None, stage=None):
#     g = json.load(open('/home/veronica/hockeystats/ver3/game_indexes/' + season + '.json'))#13_20242025_playoffs.json'))
#     all_games = [k['id'] for k in g['games']]
#     games = all_games#[:20] # gam[168742]
#     res={}
#     flat_res = []
#     ctr = 0
#     for game in games:
#         ctr += 1
#         print(f"Game {game} ({ctr} of {len(games)})")
#         game_info, shift_info, roster, playsequence, playsequence_compiled = file_tools.get_game_dicts(game)
#
#         game_end_time = int(np.ceil(playsequence['events'][-1]['game_time']))
#         teams = list(set([a['team_in_possession'] for a in playsequence['events'] if
#                           (a['team_in_possession'] is not None) and (not a['team_in_possession'] == 'None')]))
#
#         game_info = add_team_id_to_game_info(playsequence, roster, game_info)
#         goalies = [p for p in roster.keys() if roster[p]['position'] == "G"]
#         data = [d for d in shift_info if d['player_id'] not in goalies]
#         home_team_id = game_info['home_team']['id']
#         away_team_id = game_info['away_team']['id']
#         t=time.perf_counter()
#         data_home_team = process_shifts(data, team_id=home_team_id)
#         data_away_team = process_shifts(data, team_id=away_team_id)
#         #print(time.perf_counter() - t)
#         data_home_team = shifts_reset_on_whistle(data_home_team, playsequence)
#         data_away_team = shifts_reset_on_whistle(data_away_team, playsequence)
#         #print(time.perf_counter() - t)
#         #toi_home_team = [current_shift_time_on_ice(data_home_team, p) for p in range(0, game_end_time)]
#         #toi_away_team = [current_shift_time_on_ice(data_away_team, p) for p in range(0, game_end_time)]
#         #sd = shift_data(168742)
#         #print(time.perf_counter() - t)
#         for player in data_home_team.keys():
#             if player not in res.keys():
#                 res[player] = []
#             player_shift_lengths = [k[1]-k[0] for k in data_home_team[player]]
#             #res[player].append(
#             flat_res.append(
#                 {
#
#                     'game_id': game_info['id'],
#                     'team_id': home_team_id,
#                     'player_id': player,
#                     'player_shifts': player_shift_lengths,
#                     'n': len(player_shift_lengths),
#                     'avg': np.mean(player_shift_lengths),
#                     'std': np.std(player_shift_lengths)
#                 }
#             )
#         for player in data_away_team.keys():
#             if player not in res.keys():
#                 res[player] = []
#             player_shift_lengths = [k[1] - k[0] for k in data_away_team[player]]
#             #res[player].append(
#             flat_res.append(
#                 {
#                     'player_id': player,
#                     'game_id': game_info['id'],
#                     'team_id': home_team_id,
#                     'player_shifts': player_shift_lengths,
#                     'n': len(player_shift_lengths),
#                     'avg': np.mean(player_shift_lengths),
#                     'std': np.std(player_shift_lengths)
#                 }
#             )
#
#     return flat_res

def plot_shift_distribution(season=None, bins=30, range=[30,60]):
    season = "1_20242025_regular"
    g = json.load(open('shift_stats/' + season + '.json'))  # 13_20242025_playoffs.json'))
    hist = [k['mean'] for k in g['player_season'] if k['n'] > 0]
    plt.hist(hist, bins=bins, range=range)
    plt.show()

if __name__ == "__main__":
    ROOTPATH = "/home/veronica/hockeystats/ver3"

    team_info = json.load(open(os.path.join(ROOTPATH, "teams.json")))
    a = json.load(open("toi_all_seconds.json","r"))
    i = json.load(open("toi_scoring_chances_against.json"))
    teams = list(a.keys())


    for t in teams:#[0:1]:
        team_names = [f"{team['location']} {team['name']}" for team in team_info['teams'] if team['id'] == t]
        print(team_names)
        print(t)
        b = a[t]
        c = [p for p in b if not np.isnan(p)]
        d = [int(p) for p in c]
        toi_all_seconds = np.histogram(d,12,(0,60),density=False)

        j = i[t]
        scoring_chances = np.histogram(j,12,(0,60), density=False)

        k = 1200*scoring_chances[0] / toi_all_seconds[0]
        plt.plot([5 * i for i in range(1,13)], k) #,[5*kk for kk in range(k)])
        plt.xlabel("Average time on ice of skaters (5 vs 5)", fontsize=10)
        plt.ylabel("Scoring chances by opponent (A,B or C) per 20 min", fontsize=10)
        plt.text(x=5, y=8, s=f"{team_names[0]}", fontsize=12, color="red")
        plt.savefig(f"/home/veronica/shiftstats/{team_names[0]}.jpg")
        plt.clf()
        #plt.show()
    exit(0)



    for t in list(a.keys()):#[0:1]:
        print(t)
        vals=a[t]

        #p=np.cumsum(hist)
        #plt.plot(p, label=t)
        k=plt.hist(vals, bins=90, range=[0,90])
        print(np.mean(vals))
        print(np.std(vals))
        plt.show()
    exit(0)
    ROOTPATH = '/home/veronica/hockeystats/ver3'
    games = file_tools.game_ids([13],['20242025'])
    schedule = json.load(open(os.path.join(ROOTPATH, 'leagues','13','20242025','games.json')))
    res={}
    toi={}
    for item in tqdm(schedule['games']):
        game_data = file_tools.get_game_dicts(item["id"], ignore='playsequence_compiled')
        all_scoring_chances = data_tools.scoring_chances(game_data)  # playsequence, game_info)
        #scoring_chances_home_team = all_scoring_chances['home_team']
        #scoring_chances_away_team = all_scoring_chances['away_team']
        toi_home_team, toi_away_team = shift_data(game_data)  # game_id)

        times_in_seconds = [int(chance[0]) for chance in all_scoring_chances['away_team']]
        tois = [toi_home_team[t]['mean'] for t in times_in_seconds]
        if item['home_team_id'] not in res.keys():
            res[item['home_team_id']] = []
        res[item['home_team_id']] += tois


        times_in_seconds = [int(chance[0]) for chance in all_scoring_chances['home_team']]
        tois = [toi_away_team[t]['mean'] for t in times_in_seconds]
        if item['away_team_id'] not in res.keys():
            res[item['away_team_id']] = []
        res[item['away_team_id']] += tois

        #five_on_five_seconds = [len(list(t[0].keys())) == 6 and len(list(t[1].keys())) == 6 for t in list(zip(toi_home_team,toi_away_team))]

        toi_both_teams = [(t[0], t[1]) for t in list(zip(toi_home_team, toi_away_team)) if len(list(t[0].keys())) == 6 and len(list(t[1].keys())) == 6]
        toi_home_team = [k[0] for k in toi_both_teams]
        toi_away_team = [k[1] for k in toi_both_teams]

        if item['home_team_id'] not in toi.keys():
            toi[item['home_team_id']] = []
        toi[item['home_team_id']] += [t['mean'] for t in toi_home_team]

        if item['away_team_id'] not in toi.keys():
            toi[item['away_team_id']] = []
        toi[item['away_team_id']] += [t['mean'] for t in toi_away_team]

    print(res)
    with open("toi_scoring_chances_against.json", 'w') as f:
        json.dump(res, f, indent=4)
    with open("toi_all_seconds.json", 'w') as f:
        json.dump(toi, f, indent=4)
    exit(0)
    print(games)
    #games = [139104,139105]
    #res = aggregated_average_shift_lengths(games)
    #print(res)
    exit(0)
    #plot_shift_distribution(season="13_20242025_playoffs")
    #exit(0)

    season = "13_20242025_playoffs"
    flat_res = average_shift_length_all_players(season)
    final_flat_res = {'all_shifts': flat_res}
    #with open("shift_lenghts_tmp.json", "w") as f:
    #    json.dump(final_flat_res, f, indent=4)

    psa = player_shift_average(final_flat_res)
    with open("shift_stats/" + season + ".json", "w") as f:
        json.dump(psa, f, indent=4)
    print(psa)