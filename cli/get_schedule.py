import argparse
import sys
sys.path.insert(1, '../')

import scraping
import os

root_dir = '/home/veronica/repos/HockeyStats_clean'
def run(team_sl_id, path=".", regular_season=True, season="2022-23"): #args):
    url = f'https://hockey.sportlogiq.com/teams/{team_sl_id}/schedule'
    scraping.download_schedule(url, path, regular_season)
    return



if __name__ == '__main__':
    os.chdir(root_dir)
    parser = argparse.ArgumentParser()
    parser.add_argument("team_sl_id", type=int)
    parser.add_argument("--season", type=str, default="2022-23")
    parser.add_argument("--regular_season", type=bool, default=True)
    parser.add_argument("--path", type=str, default='.')
    args = parser.parse_args()
    run(args.team_sl_id, regular_season=args.regular_season, path=args.path, season=args.season)
