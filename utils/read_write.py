import os
from pathlib import Path
import uuid

map = {'id':'id','game_id': 'gameReferenceId', 'expected_goals_all_shots': 'expectedGoalsAllShots',
       'expected_goals_on_net': 'expectedGoalsOnNet',
       'flags': 'flags', 'game_time': 'gameTime', 'sl_id': 'id', 'is_defensive_event': 'isDefensiveEvent',
       'is_last_play_of_possession': 'isLastPlayOfPossession', 'is_possession_breaking': 'isPossessionBreaking',
       'is_possession_event': 'isPossessionEvent', 'manpower_situation': 'manpowerSituation', 'name': 'name',
       'outcome': 'outcome', 'period': 'period', 'period_time': 'periodTime',
       'play_in_possession': 'currentPlayInPossession',
       'play_zone': 'playZone', 'possession_id': 'currentPossession', 'previous_name': 'previousName',
       'previous_outcome': 'previousOutcome', 'previous_type': 'previousType', 'player_id': 'playerReferenceId',
       'team_goalie_id': 'teamGoalieOnIceRef', 'opposing_team_goalie_id': 'opposingTeamGoalieOnIceRef',
       'score_differential': 'scoreDifferential', 'shorthand': 'shorthand',
       'team_in_possession': 'teamInPossession', 'team_skaters_on_ice': 'teamSkatersOnIce', 'timecode': 'timecode',
       'video_frame': 'frame', 'x_adjacent_coordinate': 'xAdjCoord', 'x_coordinate': 'xCoord',
       'y_adjacent_coordinate': 'yAdjCoord', 'y_coordinate': 'yCoord', 'zone': 'zone', 'type': 'type',
       'players_on_ice': 'apoi', 'player_on_ice':'apoi'}

def string_to_file(data, parent_dir, filename=None):
    if filename is None:
        filename = str(uuid.uuid4())
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    with open(os.path.join(parent_dir, filename),'w+') as f:
        f.write(data)

    print('Wrote ' + str(len(data)) + ' to ' + os.path.join(parent_dir, filename))


def load_events(df):
    inv_map = {map[key]:key for key in map.keys()}
    df = df.rename(columns=inv_map)
    return df



