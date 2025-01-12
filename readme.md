Step 1.

# ETL
## Download leaguefile
Begin by manually save the html-code for the dropdownbox where the league is selected.
This code contains the sportlogiqs team-codes and names. Extract the teamnames by:

`teams = scraping.extract_teams_from_league('/home/veronica/hockeystats/SHL/2023-24/league.html')`

This returns a json object with the teamnames:
`
[{'sl_id': 130, 'sl_name': 'Färjestad'},
 {'sl_id': 310, 'sl_name': 'Frölunda'},
 {'sl_id': 129, 'sl_name': 'HV71'},
 {'sl_id': 806, 'sl_name': 'IK Oskarshamn'},
 {'sl_id': 324, 'sl_name': 'Leksands'},
 {'sl_id': 309, 'sl_name': 'Linköping'},
 {'sl_id': 179, 'sl_name': 'Luleå'},
 {'sl_id': 2080, 'sl_name': 'MODO'},
 {'sl_id': 126, 'sl_name': 'Malmö'},
 {'sl_id': 201, 'sl_name': 'Örebro'},
 {'sl_id': 128, 'sl_name': 'Rögle'},
 {'sl_id': 82, 'sl_name': 'Skellefteå'},
 {'sl_id': 617, 'sl_name': 'Timrå'},
 {'sl_id': 200, 'sl_name': 'Växjö'}]`

Now, for each team find the teams id in the database by comparing the names if they exist.

`
 teams = db_tools.create_teamname_map(teams)
`

`
[{'sl_id': 130, 'sl_name': 'Färjestad', 'id': 7, 'name': 'Färjestad'},
 {'sl_id': 310, 'sl_name': 'Frölunda', 'id': 6, 'name': 'Frölunda'},
 {'sl_id': 129, 'sl_name': 'HV71', 'id': 8, 'name': 'HV71'},
 {'sl_id': 806, 'sl_name': 'IK Oskarshamn', 'id': 13, 'name': 'Oskarshamn'},
 {'sl_id': 324, 'sl_name': 'Leksands', 'id': 9, 'name': 'Leksand'},
 {'sl_id': 309, 'sl_name': 'Linköping', 'id': 10, 'name': 'Linköping'},
 {'sl_id': 179, 'sl_name': 'Luleå', 'id': 11, 'name': 'Luleå'},
 {'sl_id': 2080, 'sl_name': 'MODO', 'id': 81, 'name': 'Modo Hockey'},
 {'sl_id': 126, 'sl_name': 'Malmö', 'id': 3, 'name': 'Malmö'},
 {'sl_id': 201, 'sl_name': 'Örebro', 'id': 18, 'name': 'Örebro'},
 {'sl_id': 128, 'sl_name': 'Rögle', 'id': 15, 'name': 'Rögle'},
 {'sl_id': 82, 'sl_name': 'Skellefteå', 'id': 16, 'name': 'Skellefteå'},
 {'sl_id': 617, 'sl_name': 'Timrå', 'id': 2, 'name': 'Timrå'},
 {'sl_id': 200, 'sl_name': 'Växjö', 'id': 17, 'name': 'Växjö'}]
`

This json object is stored in the file 'tmp/map.json'. Verify that the teams are mapped correctly.
If not, update in tmp.json and use the corrected map when storing the teams.

`
teams = db_tools.load_teams_from_file('tmp/map.json')
`

Now use the corrected map to store the teams and to assign them to a competition.

`
    db_tools.store_teams(teams)
    db_tools.assign_teams(teams, '2023-24', 1)
`

Next download the schedules for each team in the comptetition:

`
scraping.download_schedules(league_file, './tmp', regular_season=True)
`

Store the games for each team. If necessary, pass the team-map created previously to make sure the teamnames
are mapped correctly.

`
store_games_from_schedules("/home/veronica/hockeystats/SHL/2023-24/playoff/schedules", 1, 'PLY', teams_map="team_names_map_640dace7-a24d-4711-b67d-7f99b5dd604e")
`

Download gamefiles:
`
sql = f"select sl_game_id from game where league_id = 4 and date > \'2024-09-01\' and date < \'2024-12-13\';"
game_ids = extract_games_from_db(sql)
scraping.download_gamefiles(game_ids, src_dir='/home/veronica/hockeystats/SHL/2023-24/playoff/gamefiles')
`
    
Use the gamefiles to store the players in each game:

`
root_dir='/home/veronica/hockeystats/Hockeyallsvenskan/2024-25/regular-season/gamefiles'

files = os.listdir(root_dir)
for file in [os.path.join(root_dir,f) for f in files]:
    db_tools.store_players(file)
`

Store the events from each game:

`
ctr = 0
for file in [os.path.join(root_dir,f) for f in files]: #[470:]:
    print(f"{ctr} of {len(files)} {file}")
    db_tools.store_events(file)
    ctr += 1
`