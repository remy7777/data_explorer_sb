import pandas as pd
import numpy as np
from mplsoccer import Sbopen
import warnings
warnings.filterwarnings("ignore")
import sys

sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_type import get_event_type

def pass_matrix(competition_id, season_id, home_team, away_team):
    """
    Generate a pass matrix for a football match.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        pandas.io.formats.style.Styler: A styled pass matrix.

    This function generates a pass matrix for a football match. It retrieves passer and receiver data, filters and processes
    the data, and creates a pass matrix showing the number of passes from each player to another player. The matrix is
    styled with a blue gradient.

    Example:
        pass_matrix(123, 2022, "Team A", "Team B")
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    passer_df = get_event_type(away_team_id, "Pass")
    receiver_df = get_event_type(away_team_id, "Ball Receipt")

    HOME = home_team
    AWAY = away_team

    home_passes = passer_df[(passer_df["play_pattern_name"] == "Regular Play") & 
                            (passer_df["team_name"] == HOME)]

    home_passes = home_passes[["period", "minute", "match_id", "team_name", 
                                "player_name", "position_name", "end_x", "end_y"]]

    home_passes.rename(columns={"player_name":"passer", "position_name":"passer_position"}, inplace=True)

    home_receivers = receiver_df[(receiver_df["play_pattern_name"] == "Regular Play") & 
                                (receiver_df["team_name"] == HOME)]

    home_receivers = home_receivers[["player_name", "position_name", "x", "y"]]
    home_receivers.rename(columns={"player_name":"receiver", "position_name":"receiver_position"}, inplace=True)

    merged_df = pd.merge(home_passes, home_receivers, left_on="end_x", right_on="x", how="inner")
    merged_df = merged_df[merged_df["passer"] != merged_df["receiver"]]
    pass_matrix = pd.crosstab(merged_df["passer"], merged_df["receiver"], margins=True, margins_name="Total")
    pass_matrix = pass_matrix.style.background_gradient(cmap="Blues")

    return pass_matrix


