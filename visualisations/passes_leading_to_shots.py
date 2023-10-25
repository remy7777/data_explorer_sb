import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mplsoccer import Sbopen, Pitch, add_image, VerticalPitch
from highlight_text import ax_text
import warnings
warnings.filterwarnings("ignore")
import sys

sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_df import get_event_df

def passes_leading_to_shots(competition_id, season_id, home_team, away_team):
    """
    Generate a visualization of passes leading to shots in a football match.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        None

    This function generates a visualization of passes leading to shots in a football match. It retrieves event data,
    filters and processes the data to identify passes leading to shots, and creates a plot showing the passes and
    corresponding shots. The plot is saved as a file named "passes_to_shots".

    Example:
        passes_leading_to_shots(123, 2022, "Team A", "Team B")
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    df = get_event_df(away_team_id)

    TEAM1 = home_team
    TEAM2 = away_team

    df_pass = df.loc[(df["pass_assisted_shot_id"].notnull()) & (df["team_name"] == home_team),
                    ["x", "y", "end_x", "end_y", "pass_assisted_shot_id"]]

    df_shot = (df.loc[(df["type_name"] == "Shot") & (df["team_name"] == home_team),
                    ["id", "outcome_name", "shot_statsbomb_xg"]]
            .rename({"id": "pass_assisted_shot_id"}, axis=1))

    df_pass = df_pass.merge(df_shot, how="left").drop("pass_assisted_shot_id", axis=1)

    mask_goal = df_pass["outcome_name"] == "Goal"

    # Setup the pitch
    pitch = VerticalPitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc",
                        half=True, pad_top=2)
    fig, axs = pitch.grid(endnote_height=0.03, endnote_space=0, figheight=12,
                        title_height=0.08, title_space=0, axis=False,
                        grid_height=0.82)
    fig.set_facecolor("#22312b")

    # Plot the completed passes
    pitch.lines(df_pass["x"], df_pass["y"], df_pass["end_x"], df_pass["end_y"],
                lw=10, transparent=True, comet=True, cmap="jet",
                label="pass leading to shot", ax=axs["pitch"])

    # Plot the goals
    pitch.scatter(df_pass[mask_goal].end_x, df_pass[mask_goal].end_y, s=700,
                marker="football", edgecolors="black", c="white", zorder=2,
                label="goal", ax=axs["pitch"])
    pitch.scatter(df_pass[~mask_goal].end_x, df_pass[~mask_goal].end_y,
                edgecolors="white", c="#22312b", s=700, zorder=2,
                label="shot", ax=axs["pitch"])

    axs["title"].text(0.5, 0.5, f"{TEAM1} passes leading to shots \n vs {TEAM2}", color="#dee6ea",
                    va="center", ha="center", fontsize=25)

    #plt.savefig("passes_to_shots")
    plt.show()


