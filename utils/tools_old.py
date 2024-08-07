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

def extract_game_info_from_schedule_html(filename):
    html = open(filename,'r').read()
    months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    year_adds = [1,1,1,1,1,1,1,0,0,0,0,0]
    year = 2023
    months_start_pos = []
    for (idx, month) in enumerate(months):
        res = re.search(f"\"month-label\">{month}", html)
        if res:
            months_start_pos.append((idx, res.start()))


    months_start_pos = sorted(months_start_pos, key=lambda x:(x[1]))
    try:
        months_end_pos = months_start_pos[1:]+[tuple(np.array(months_start_pos[-1]) + ((0,len(html))))]
    except:
        print('apa')
    parts = []
    for i in range(0, len(months_start_pos)):
        parts.append(months_start_pos[i] + (months_end_pos[i][1],))
    games = []
    for (month, start, end) in parts:
        crop = html[start:end]
        rows = crop.split('season-schedule-row')[1:]
        for row in rows:
            home_team = row.split('matchup-content\">')[2].split('<')[0] #.replace(' ','')
            away_team = row.split('matchup-content\">')[1].split('<')[0] #.replace(' ','')
            date = str(year + year_adds[month]) + str(month + 1).zfill(2)  +\
                   re.findall('\d+', row.split('date-container')[1])[0].zfill(2)
            sl_game_id = row.split('/games/league/')[1].split('/')[0]
            games.append((home_team, away_team, date, sl_game_id))
            print(date + ' ' + home_team + ' ' + away_team)


    return games
