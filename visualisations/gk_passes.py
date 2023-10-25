import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Sbopen, Pitch, VerticalPitch
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_type import get_event_type

def gk_passmap(competition_id, season_id, home_team, away_team):
    """
    Generate a passmap for the goalkeeper's passes in a match.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    This function generates a passmap for the goalkeeper's passes in a match. It retrieves goalkeeper passes
    from the specified competition, season, home team, and away team. The passmap is displayed on a vertical pitch
    with different colors indicating pass types (High Pass, Ground Pass, Low Pass). Each pass is represented by a
    line, and the end point is marked with a triangle marker. Arrows indicate the direction of the passes.

    Example:
        gk_passmap(123, 2022, "Team A", "Team B")
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team) 
    passes = get_event_type(away_team_id, "Pass")
    gk_passes = passes[(passes["position_name"] == "Goalkeeper") & (passes["team_name"] == home_team)
                        & (passes["play_pattern_name"] == "Regular Play")]

    # Create a Vertical Pitch
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc")

    # Set up the figure and axis
    fig, ax = pitch.draw(figsize=(5,5))
    fig.patch.set_facecolor("#22312b")

    # Define color mapping for pass types
    pass_type_colors = {"High Pass": "red", "Ground Pass": "yellow", "Low Pass": "blue"}  

    legend_elements = [plt.Line2D([0], [0], color=color, lw=2, label=pass_type) 
                    for pass_type, color in pass_type_colors.items()]

    # Loop through the passes and plot them
    for index, pass_data in gk_passes.iterrows():
        start_point = (pass_data["x"], pass_data["y"])
        end_point = (pass_data["end_x"], pass_data["end_y"])
        pass_type = pass_data["pass_height_name"]
        
        # Get color based on pass type, default to black if not found
        pass_color = pass_type_colors.get(pass_type, "black")
        
        # Plot the pass with the determined color
        ax.plot([start_point[0], end_point[0]], [start_point[1], end_point[1]], color=pass_color, lw=2, zorder=1)
        
        # Plot end point with triangle marker
        ax.plot(end_point[0], end_point[1], 'o', color=pass_color, markersize=6, zorder=2)

        # Add arrow annotation
        ax.annotate('', end_point, start_point, arrowprops={'arrowstyle': '->', 'color': pass_color, 'lw': 2}, zorder=2)

    # Add title and show the plot
    gk_name = str(gk_passes["player_name"].iloc[0])
    plt.title(f"{gk_name}'s Passes", color="white")
    ax.legend(handles=legend_elements, loc="upper right")

    #plt.savefig(f"{gk_name}_passes.png")
    plt.show()







