
import numpy as np
import matplotlib
matplotlib.use('TkAgg')

APOI = None


def extract_teams(df):
    nan = np.nan
    teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    return teams.tolist()
def extract_all_players(df):
    players = []
    nan = np.nan
    teams = df.query("teamInPossession not in [@nan, 'None']").teamInPossession.unique()
    res = {}
    res[teams[0]] = []
    res[teams[1]] = []
    for team in teams:
        df_team = df.loc[df['teamInPossession'] == team]
        df_team = df_team.loc[df_team['isPossessionEvent']]
        df_team = df_team.dropna(subset=['playerReferenceId'])
        players = df_team.playerReferenceId.unique().tolist()
        #goalies = df_team.teamGoalieOnIceRef.unique().tolist()
        #players = skaters + goalies
        for player in players:
            print(player)
            df_player = df_team.loc[df_team['playerReferenceId'] == player].iloc[0]
            player = df_player.loc[['playerJersey', 'playerFirstName', 'playerLastName']]
            res[team].append(dict(player))
            print(df_player['playerFirstName'])
    return res
