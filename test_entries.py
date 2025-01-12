import db_tools
import entries
import numpy as np
from utils import read_write

nan = np.nan
team_id = 75;
league_id = 4
stats_db = db_tools.open_database()
cursor = stats_db.cursor()
teams = [13, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 84]

cursor.execute("select team.id, team.name from team join participation on team.id=participation.team_id where participation.league_id=4 and season ='2024-25';")
teams = cursor.fetchall()
season = '2024-25'

for team_id, team_name in teams:
    sql = f"select id from game where (home_team_id={team_id} or away_team_id={team_id}) and date > \'2024-07-01\' and date < \'2025-01-11\';"
    cursor.execute(sql)
    games = cursor.fetchall()
    print(len(games))
    game_ids = [g[0] for g in games]
    #cursor.execute("select team.id from team join participation on team.id=participation.team_id where participation.league_id=4 and season ='2024-25';")
    #teams = cursor.fetchall()



    game_statistics = []
    #game_ids = [5963]
    oz_rallies = []
    for idx, game_id in enumerate(game_ids):
        teams = db_tools.teams_in_game(game_id)
        df = db_tools.get_events_from_game_with_team(game_id)
        if len(df) == 0:
            print("Empty")
        else:
            a,b,c,d = entries.puck_zone(df, team_id=teams['home_team_id']) #, teams=[75,73])
            num_long_oz = len([r[5] for r in a if r[5] > 40])
            oz_rallies.append(num_long_oz)
            print(team_name, ' ', oz_rallies)

    with open(f"/home/veronica/repos/HockeyStats_clean/tmp/{team_name}.txt",'w') as file:
        res = " ".join([str(r) for r in oz_rallies])
        res = team_name + ' ' + res
        file.write(res)
        file.close()



