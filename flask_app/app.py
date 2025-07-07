from flask import Flask, render_template, request, redirect, url_for, jsonify
import matplotlib.pyplot as plt
import io
import base64
import requests
import os
import json
import entries
import pandas as pd


app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['UPLOADED_GAMES'] = []
app.config['SELECTED_STAT'] = (None, None)

def visualize(oz_entries, intervals=3):
    valid_times = [entry['time_to_first_shot'] for entry in oz_entries if entry['time_to_first_shot'] is not None]

    if not valid_times:
        raise ValueError("No valid 'time_to_first_shot' data available.")

    min_time = min(valid_times)
    max_time = max(valid_times)
    bins = list(range(int(min_time), int(max_time) + intervals, intervals))

    plt.figure(figsize=(8, 5))
    plt.hist(valid_times, bins=bins, edgecolor='black')
    plt.xlabel('Time to First Shot (seconds)')
    plt.ylabel('Frequency')
    plt.title('Histogram of Time to First Shot')

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')

@app.route('/upload_page')
def upload_file():
    return render_template('upload.html')

@app.route('/')
def main():
    return render_template('upload.html')

@app.route('/draw')
def histogram():
    # Example data
    oz_entries = [
        {'time_to_first_shot': 4.5},
        {'time_to_first_shot': 7.2},
        {'time_to_first_shot': 2.1},
        {'time_to_first_shot': None},
        {'time_to_first_shot': 5.0},
        {'time_to_first_shot': 10.4},
        {'time_to_first_shot': 6.7},
    ]
    plot_url = visualize(oz_entries, intervals=3)
    return render_template('entries_histogram.html', plot_url=plot_url)


@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    # Save the file in the specified folder
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    # while file.filename not in os.listdir('data'):
    #     sleep(1)
    # files = os.listdir('data')

    process_file(file.filename)

    return redirect(url_for('upload_file'))

@app.route('/games')
def games():

    games = [{'game_id': g['game_id'], 'team1': g['team_1'], 'team2': g['team_2']} for g in app.config['UPLOADED_GAMES']]
    return render_template('games.html', games=games)

@app.route('/team_stats', methods=['POST'])
def team_stats():
    print(app.config['UPLOADED_GAMES'])
    data = request.json
    game_id = data['game_id']
    team_name = data['team_name']
    print(game_id)
    print(team_name)

    entry_stats = [g for g in app.config['UPLOADED_GAMES'] if g['game_id'] == game_id]
    visual = None
    print(entry_stats)
    if len(entry_stats) == 1:
        entry_stats = entry_stats[0]
    # Call your Python function here
        if entry_stats['team_1'] == team_name:
            visual = visualize(entry_stats['stat_team_1'])
        else:
            visual = visualize(entry_stats['stat_team_2'])

    return jsonify({'stats': visual})


def process_file(filename):
    with open(f"data/{filename}", "r") as f:
        events = json.load(f)

    c_map = entries.get_map()
    df = pd.DataFrame.from_dict(events['events'])
    df = df.rename(columns=c_map[0])
    oz_rallies = entries.get_oz_rallies(df)
    teams = [t for t in list(oz_rallies.keys()) if t is not None]
    tts_t1 = entries.time_entry_to_shots(oz_rallies[teams[0]])
    tts_t2 = entries.time_entry_to_shots(oz_rallies[teams[1]])

    tts_t1 = [e['rally_stat'] for e in tts_t1]
    tts_t2 = [e['rally_stat'] for e in tts_t2]

    app.config['UPLOADED_GAMES'].append(
        {
            'game_id': filename.split('.')[0],
            'team_1': teams[0],
            'stat_team_1': tts_t1,
            'team_2': teams[1],
            'stat_team_2': tts_t2
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
