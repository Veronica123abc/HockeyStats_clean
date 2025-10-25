from flask import Flask, render_template, send_file, redirect, url_for
import os

app = Flask(__name__)

GAMES_DIR = "generated/games"

@app.route("/")
def index():
    games = []
    for game_id in sorted(os.listdir(GAMES_DIR)):
        game_path = os.path.join(GAMES_DIR, game_id)
        meta_path = os.path.join(game_path, "game-metadata.txt")
        if os.path.isdir(game_path) and os.path.isfile(meta_path):
            with open(meta_path, "r") as f:
                description = f.read().strip()
            games.append({"id": game_id, "description": description})
    return render_template("index.html", games=games)

@app.route("/game/<game_id>")
def game_page(game_id):
    game_path = os.path.join(GAMES_DIR, game_id)
    oz_path = os.path.join(game_path, "oz-entries.html")
    shift_path = os.path.join(game_path, "shift-data.html")

    oz_content = ""
    shift_content = ""

    if os.path.exists(oz_path):
        with open(oz_path, "r") as f:
            oz_content = f.read()
    if os.path.exists(shift_path):
        with open(shift_path, "r") as f:
            shift_content = f.read()

    return render_template("game.html", game_id=game_id,
                           oz_entries=oz_content,
                           shift_data=shift_content)
