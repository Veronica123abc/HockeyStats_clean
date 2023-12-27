import pandas as pd
import re
import numpy as np
import math

APOI = None

def shot_assist(df=None, filename=None, player_id=None):
    passes_and_shots = df[(df['name'] == 'pass') + (df['name'] == 'shot')]
    successful_passes_and_shots = passes_and_shots.loc[passes_and_shots['outcome'] == 'successful']
    shots_idx = list(successful_passes_and_shots['name'] == 'shot')
    shot_assists_idx = shots_idx[1:] + [False]
    shot_assists = successful_passes_and_shots[shot_assists_idx]
    player_shot_assists = shot_assists[shot_assists['playerReferenceId'] == player_id]
    return player_shot_assists.shape[0]

def convert_to_int(n):
    n = convert_to_string(n)
    if len(n) > 0:
        return int(float(n))
    else:
        return None

#    if isinstance(n, float):
#        return n
#    elif isinstance(n, int):
#        return n
#    elif isinstance(n, str):
#        return int(re.sub("[^0-9]", " ", n))


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

def all_players_in_game(df):
    apoi = all_players_on_ice(df)
    apig = list(set([int(float(s)) for s in ''.join(apoi).split(' ') if len(s) > 0]))

    return apig

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


def get_player_ids(df=None, filename=None, team=None):
    players = list(df.query("team == @team").playerReferenceId.astype({'playerReferenceId': 'int'}).unique())
    return players

def time_on_ice(df=None, player_id=None):
    woi = player_on_ice(df, str(player_id))
    game_times = df['gameTime']
    event_duration = list(np.array(game_times)[1:] - np.array(game_times)[0:-1])
    toi = sum(np.array(event_duration)[list(woi.index)])
    m,s = divmod(round(toi),60)
    return f'{m:02d}:{s:02d}'

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

def generate_summary(filename=None, team=None):
    df = pd.read_csv(filename)
    nan = np.nan
    teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    team_1 = generate_summary_for_team(df=df, team=teams[0])
    team_2 = generate_summary_for_team(df=df, team=teams[1])
    team_1.to_csv('team_1.csv')
    team_2.to_csv('team_2.csv')

    #return team_1, team_2

def generate_summary_for_team(df=None, filename=None, team=None):

    players = get_player_ids(df=df, team=team)
    print(players)
    fields = ['NR', 'Name','Position','TOI','Shots on Net from slot (ES)',
              'Shots on Net from outside (ES)', 'Shot Assists (ES)', 'Shots on Net For WOI (ES)',
              'Shots on Net Against WOI (ES)','Passes to slot for WOI (ES)', 'Passes to slot against WOI (ES)', 'OGP/20',
              'Turnovers', 'Takeaways','G', 'A', 'TOT', 'PIM','Blocked Shots', 'Plus/Minus','tek+', 'tek tot', 'tek %',
              'Shots on net (PP)', 'Shot attempts (PP)', 'Shots on net against (PP)', 'Shot attempts against (PP)']

    output = pd.DataFrame(columns=fields)

    for player_id in players:
        # Begin with Even Strength metrics
        even_strength = df.query("manpowerSituation == 'evenStrength'")
        personal = even_strength.query("playerReferenceId == @player_id")
        #s = time.time()
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
        successful_possession_plays = personal.query("isPossessionEvent and outcome != 'successful'").shape[0]
        total_possession_plays = personal.query("isPossessionEvent").shape[0]
        turnover_rate = float(successful_possession_plays) / float(total_possession_plays+0.00000001)
        takeaways = 0
        personal = df.query("playerReferenceId == @player_id")
        p_m = plus_minus(df=df, player_id=player_id,team=team)
        faceoffs_won = 0
        faceoffs_total = 0
        faceoff_percent = 0
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
                   passes_to_slot_for_woi, passes_to_slot_against_woi, ogp_20, turnover_rate, takeaways,
                   goals, assists, points, penalties, blocked_shots, p_m, faceoffs_won, faceoffs_total, faceoff_percent,
                   shots_on_net_pp, shot_attempts_pp, shots_on_net_against_sh, shot_attempts_against_sh]

        output.loc[len(output.index)] = new_row
    return output

