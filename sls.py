import argparse
import data_collection
import argparse
import time
import json
import os
from datetime import datetime
from utils.shifts import scoring_chances_vs_shifts_lengths
ROOTPATH = "/home/veronica/hockeystats/ver3"

def download(args):
    print(args)
    data_collection.download_complete_games(game_ids=args.game_ids, verbose=False)

def verify(game_ids, shifts=False, save_to_file=False):
    if shifts:
        incomplete_games = data_collection.verify_shift_times(game_ids)
        if len(incomplete_games['incomplete']) > 0:
            download_query = input("\nDo you want to fix the shift-times in the incomplete games? [y or N]: ")
            if download_query in ['y', 'Y', 'yes']:
                print('Adding period times to shifts ...')
                data_collection.add_period_time_to_shifts(game_ids = incomplete_games['incomplete'])

    else:
        incomplete_games = data_collection.verify_downloaded_games(game_ids)
        for k in list(incomplete_games.keys()):
            print(f"{k}: {incomplete_games[k]}")
        if len(incomplete_games['incomplete']) > 0:
            download_query = input("\nDo you want to download the incomplete games? [y or N]: ")
            if download_query in ['y', 'Y', 'yes']:
                print('Beginning to download ...')
                data_collection.download_complete_games(game_ids=incomplete_games['incomplete'])

def set_leagues(args):
    updated = False
    with open("sls_settings.json", "r") as f:
        settings = json.load(f)

    if args.league_action == 'list':
        print(settings["scope"]["leagues"])
    if args.league_action == 'add':
        league_ids = [l for l in args.league_ids if l.isnumeric()]
        settings["scope"]["leagues"] += league_ids
        settings["scope"]["leagues"] = list(set(settings["scope"]["leagues"]))

        updated = True
    elif args.league_action == 'remove':
        league_ids = [l for l in args.league_ids if l.isnumeric()]
        settings["scope"]["leagues"] = [l for l in settings["scope"]["leagues"] if l not in league_ids]
        updated = True
    if updated:
        with open("sls_settings.json", "w") as f:
            json.dump(settings, f, indent=4)



def recent_games(args):
    with open("sls_settings.json", "r") as f:
        settings = json.load(f)

    leagues = settings["scope"]["leagues"]
    seasons = settings["scope"]["seasons"] #['20242024']
    stages = settings["scope"]["stages"] #['regular', 'playoffs']
    games = data_collection.recent_games(league_ids=leagues,seasons=seasons, stages = stages, days_delta=args.days, date_to=args.to)
    recent_game_ids = [g['id'] for g in games]

    if args.verify_recent_games:
        downloaded_games = [game_id for game_id in recent_game_ids if os.path.exists(os.path.join(ROOTPATH, str(game_id)))]
        incomplete_games = data_collection.verify_downloaded_games(game_ids=downloaded_games)['incomplete']
        missing_games = [g for g in recent_game_ids if g not in downloaded_games]
        #for g in games:
        # print(' '.join([g['id'] for g in games]))
        #print(' '.join([g['id'] for g in games]))
        #print(len(incomplete_games + missing_games))
        print(f"There are {len(recent_game_ids)} finished games in the selected scope.")
        print(f"Out of these games, there are {len(missing_games)} not downloaded and {len(incomplete_games)} incompletey downloaded.")
        download_query = input("\nBegin to download the recent games? [y or N]")
        if download_query in ['y', 'Y']:
            data_collection.download_complete_games(game_ids=missing_games+incomplete_games)

    else:
        print(f"{len(recent_game_ids)} games were found.")
        print(recent_game_ids)

def download_games(game_index_file=None, game_ids=None, update=False):
    data_collection.download_complete_games(game_index_file, game_ids, update)

def parse_league_ids(value):
    # Split on comma, strip whitespace, convert to int
    try:
        return [int(v.strip()) for v in value.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError("All league IDs must be integers separated by commas.")

def fix_shifts(args):
    games = args.game_ids
    data_collection.add_period_time_to_shifts(games)

def shifts_scoring(args):
    for game_id in args.game_ids:
        scoring_chances_vs_shifts_lengths(game_id)

def main():
    parser = argparse.ArgumentParser(prog="sls", description="Simple CLI with subcommands")
    subparsers = parser.add_subparsers(dest="command")


    # Subcommand verify
    parser_shifts = subparsers.add_parser("shift")
    parser_verify = subparsers.add_parser("verify", help="Verify downloaded items")
    parser_download = subparsers.add_parser("download", help="Download game(s)")
    parser_fix_shifts = subparsers.add_parser("fix_shifts", help="Add period time to shifts")
    parser_fix_shifts.add_argument("-g", "--game_ids", nargs="*", help="Game IDs to fix")
    parser_download.add_argument("-g", "--game_ids", nargs="*", help="Game IDs to download")
    parser_recent_games = subparsers.add_parser("games", help="Check new games")
    parser_recent_games.add_argument("--verify", dest='verify_recent_games', help="Verify if the recent games are downloaded", action='store_true')
    parser_recent_games.add_argument("--days",
                                     type=str, help="Number of days back in time to check. Default is 7. 0 means games finished today.", default='7')
    parser_recent_games.add_argument("--to",
                                     type=str, help="Last day of interval", default=datetime.now().strftime("%Y%m%d"))
    parser_league = subparsers.add_parser("league", help="Add or remove league(s) to scope")
    parser_verify.add_argument("--game_ids", type=int, nargs="*", default=None, help="Games for which to check downloaded items")
    parser_verify.add_argument("--shifts", dest='shifts', action='store_true', help="Check if shifts contain period-time")
    parser_verify.add_argument("--save_to_file", dest='save_to_file', action='store_true', help="Save the results to file in json format")
    #parser_verify.add_argument("--res_file_name", type=str, default=None, nargs='?')
    #parser_verify.add_argument("--res_file_name", default='non_complete_games.json')
    parser_verify.add_argument("-r", dest='res_file_name', type=str, nargs='?', help="Filename where results should be saved to.")


    subparsers_league = parser_league.add_subparsers(dest = "league_action")
    league_parser_add = subparsers_league.add_parser("add")
    league_parser_remove = subparsers_league.add_parser("remove")
    league_parser_list = subparsers_league.add_parser("list")
    league_parser_add.add_argument("league_ids", type=str, nargs='+', help="League(s) to add to scope.")
    #league_parser_add.add_argument("league_ids", type=parse_league_ids, nargs='?', help = "League(s) to add to scope.")
    league_parser_remove.add_argument("league_ids", type=str, nargs='+', help="League(s) to remove from scope.")
    #league_parser_list.add_argument("league_ids", type=bool, default=True, help="List leagues in scope.")
    parser_shifts.add_argument("-g", "--game_ids", nargs="*", help="Game IDs to fix")
    parser_shifts.add_argument("-f", "--filename", help="Filename where results should be saved to.")

    args = parser.parse_args()

    if args.command == "shift":
        shifts_scoring(args)
    elif args.command == "verify":
        if not args.save_to_file:
            args.res_file_name = None
        if args.shifts:
            verify(args.game_ids, shifts=True)
        else:
            verify(args.game_ids, save_to_file=args.res_file_name)#save_to_file=args.save_to_file)
    elif args.command == "games":
        recent_games(args)
    elif args.command ==  "league":
        set_leagues(args)
    elif args.command == "download":
        download(args)
    elif args.command == "fix_shifts":
        fix_shifts(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
