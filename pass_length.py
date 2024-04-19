import pandas as pd
import re
import numpy as np
import math
import db_tools

def pass_analysis(df=None, team=None):
    df = df[(df['team_in_possession'] == team)]
    passes = df[(df['name'] == 'pass')]
    receptions = df[(df['name'] == 'reception')]
    successful_passes = passes.loc[passes['outcome'] == 'successful']
    successful_receptions = receptions.loc[receptions['outcome'] == 'successful']

    pass_positions = [np.array(p) for p in list(successful_passes[['x_coordinate', 'y_coordinate']].itertuples(
        index=False, name=None))]
    reception_positions = [np.array(p) for p in list(successful_receptions[['x_coordinate', 'y_coordinate']].itertuples(
        index=False, name=None))]
    distances = [np.linalg.norm(p[0]-p[1]) for p in zip(pass_positions, reception_positions)]
    average_pass_length = sum(distances) / float(len(distances))
    return sum(distances), average_pass_length
