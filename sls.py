import argparse
import data_collection
import argparse
import time

def test1(name):
    print(f"Test 1, {name}!")

def test2(count):
    for i in range(count):
        print("Test 2")

def verify(game_ids, shifts, save_to_file):

    uncomplete_games = data_collection.verify_downloaded_games(game_ids, check_shifts=shifts, save_to_file=save_to_file)
    for k in list(uncomplete_games.keys()):
        print(f"{k}: {uncomplete_games[k]}")

def download_games(game_index_file=None, game_ids=None, update=False):
    data_collection.download_complete_games(game_index_file, game_ids, update)



def main():
    parser = argparse.ArgumentParser(prog="sls", description="Simple CLI with subcommands")
    subparsers = parser.add_subparsers(dest="command")


    # Subcommand verify
    parser_verify = subparsers.add_parser("verify", help="Verify downloaded items")
    parser_verify.add_argument("--game_ids", type=int, default=None, help="Games for which to check downloaded items")
    parser_verify.add_argument("--shifts", dest='shifts', action='store_true', help="Check if shifts contain period-time")
    parser_verify.add_argument("--save_to_file", dest='save_to_file', action='store_true', help="Save the results to file in json formal")
    #parser_verify.add_argument("--res_file_name", type=str, default=None, nargs='?')
    #parser_verify.add_argument("--res_file_name", default='non_complete_games.json')
    parser_verify.add_argument("-r", dest='res_file_name', type=str, nargs='?', help="Filename where results should be saved to.")

    args = parser.parse_args()
    print(args)
    if not args.save_to_file:
        args.res_file_name=None
    # else:
    #     args.res_file_name=args.res_file_name[0]
    print(args)
    if args.command == "test1":
        test1(args.name)
    elif args.command == "test2":
        test2(args.count)
    elif args.command == "verify":
        verify(args.game_ids, shifts=args.shifts, save_to_file=args.res_file_name)#save_to_file=args.save_to_file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
