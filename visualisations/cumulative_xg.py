import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from mplsoccer import Sbopen
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_type import get_event_type

def cumulative_xg(competition_id, season_id, home_team, away_team):
    """
    Generate a plot showing the cumulative expected goals (xG) over time for two teams during a football match.

    Args:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        None: Saves the plot as "cumulative_xG_plot.png".

    Dependencies:
        Requires functions get_match_id, get_event_type, and get_event_df for data retrieval.

    Notes:
        This function calculates and plots the cumulative xG over intervals of 15 minutes throughout the match.
        Tactical shifts are marked on the plot for both teams.

    Example:
        cumulative_xg(competition_id=123, season_id=456, home_team='TeamA', away_team='TeamB')

    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    shot = get_event_type(away_team_id, "Shot")

    def calculate_cumulative_xG(shot_data, team, interval):
        return shot_data[(shot_data["minute"] <= interval[1]) & 
                        (shot_data["minute"] > interval[0])][shot_data["team_name"] == team]["shot_statsbomb_xg"].sum()

    def generate_cumulative_xG_array(shot_data, team, intervals):
        cumulative_xG = [0]
        for interval in intervals:
            cumulative_xG.append(cumulative_xG[-1] + calculate_cumulative_xG(shot_data, team, interval))
        return cumulative_xG

    HOME = home_team
    AWAY = away_team

    intervals = [(i, i+15) for i in range(0, 90, 15)]

    home_team_xG = [calculate_cumulative_xG(shot, HOME, interval) for interval in intervals]
    away_team_xG = [calculate_cumulative_xG(shot, AWAY, interval) for interval in intervals]
    home_team_xG.insert(0, 0) 
    away_team_xG.insert(0, 0) 

    minutes = [0, 15, 30, 45, 60, 75, 90]

    goal_home = shot[(shot["outcome_name"] == "Goal") & (shot["team_name"] == HOME)]["minute"].tolist()
    goal_away = shot[(shot["outcome_name"] == "Goal") & (shot["team_name"] == AWAY)]["minute"].tolist()

    with plt.style.context("dark_background"):
        plt.figure(figsize=(12, 7))

        plt.fill_between(minutes, home_team_xG, color='blue', alpha=0.4, label=HOME)
        plt.fill_between(minutes, away_team_xG, color='red', alpha=0.4, label=AWAY)

        # Plot goals
        plt.scatter(goal_home, [0] * len(goal_home), color='blue', label=f"{HOME} Goal", s=60, zorder=5, marker="*")
        plt.scatter(goal_away, [0] * len(goal_away), color='red', label=f"{AWAY} Goal", s=60, zorder=5, marker="*")
        
        plt.xlabel('Minute')
        plt.ylabel('Cumulative xG')
        
        plt.grid(False)
        plt.xticks(range(0, 91, 15))

        plt.legend(loc="upper left")

        #plt.savefig("cumulative_xG_plot.png")
        plt.show()







