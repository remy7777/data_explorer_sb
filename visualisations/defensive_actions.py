import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import cmasher as cmr
from PIL import Image
from urllib.request import urlopen
from mplsoccer import Sbopen, Pitch, add_image, VerticalPitch
from scipy.spatial import ConvexHull
from highlight_text import ax_text
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_df import get_event_df

def player_list(competition_id, season_id, home_team, away_team):
    """
    Get a DataFrame containing filtered event data for the home team and a list of unique player names.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        tuple: A tuple containing:
            - DataFrame: Filtered event data for the home team.
            - list: A list of unique player names.
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    df = get_event_df(away_team_id) 

    HOME = home_team

    filt = df[(df["type_name"].isin(["Block", "Foul Committed", "Clearance", "Interception"]))&
            (df["team_name"] == HOME)].dropna(axis=1)

    players = list(filt["player_name"].unique())
    return filt, players

def defensive_actions(competition_id, season_id, home_team, away_team, player):
    """
    Generate a defensive actions plot for a specific player.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.
        player (str): The name of the player for whom defensive actions are being analyzed.

    Returns:
        None

    This function generates a scatter plot of defensive actions performed by the specified player. The plot
    displays different types of defensive actions using distinct symbols and colors. The plot is saved as an
    image file with a filename based on the player's name.

    Example:
        defensive_actions(123, 2022, "Team A", "Team B", "John Doe")
    """
    filt = player_list(competition_id, season_id, home_team, away_team)[0]

    AWAY = away_team

    player_df = filt[filt["player_name"] == player].reset_index(drop=True)

    # Create a list of symbols for different type_names
    symbols = ['o', 's', '^', 'x', '+']

    # Create a list of colors for different periods
    colors = ['red', 'blue', 'green', 'purple', 'orange']

    # Create a Pitch object
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc")
    fig, ax = pitch.draw()
    fig.set_facecolor("#22312b")

    # Group the DataFrame by 'type_name'
    grouped = player_df.groupby('type_name')

    # Iterate over the groups and plot the points with different symbols and colors
    for i, (name, group) in enumerate(grouped):
        period = group['period'].iloc[0]  # Assuming 'period' is the same for all rows in a group
        ax.scatter(group['x'], group['y'], label=f"{name}", color=colors[i], marker=symbols[i], s=100)

    # Add legend
    plt.legend()

    # Add a title
    name = str(player_df["player_name"][0])
    plt.title(f"{name} Defensive Actions", c="white")

    #plt.savefig(f"{name} Defensive Actions.png")
    plt.show()



