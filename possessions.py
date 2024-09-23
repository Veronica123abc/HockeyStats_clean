import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import colors
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
APOI = None
from scipy.ndimage import interpolation
import math
import time

def puck_in_zone(df):
    teams = df.query("team_in_possession not in [@nan, 'None']").team_in_possession.unique()
    df = df['name'].dropna()
    team = teams[0]
    team_possessions = df.query("team_in_possession == @team and manpower_situation == 'evenStrength'")
    oppossing_team_possessions = df.query("team_in_possession != @team")


