import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Sbopen, Pitch, VerticalPitch
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_df import get_event_df
from get_tactics_df import get_tactics_df


def get_home_formation(competition_id, season_id, home_team, away_team):
    """
    Generates and displays the formation of the home team at the start of a football match.

    Args:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        None: Displays the formation on a football pitch.

    Dependencies:
        Requires functions get_match_id, get_event_df, and get_tactics_df for data retrieval.
        Uses the VerticalPitch class for pitch visualization.

    Notes:
        This function fetches the starting XI and corresponding formation of the home team.
        It then visualizes the formation on a football pitch using the VerticalPitch class.

    Example:
        get_home_formation(competition_id=123, season_id=456, home_team='TeamA', away_team='TeamB')
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    event = get_event_df(away_team_id)
    tactics = get_tactics_df(away_team_id)

    HOME = home_team

    starting_xi_event = event.loc[((event['type_name'] == 'Starting XI') &
                                (event['team_name'] == HOME)), ['id', 'tactics_formation']]
    # joining on the team name and formation to the lineup
    starting_xi = tactics.merge(starting_xi_event, on='id')
    formation = starting_xi['tactics_formation'].iloc[0]

    pitch = VerticalPitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(6, 8.72))
    fig.patch.set_facecolor("#22312b")

    ax_text = pitch.formation(formation, positions=starting_xi.position_id, kind='text',
                            text=starting_xi.player_name.str.replace(' ', '\n'), c="white",
                            va='center', ha='center', fontsize=10, ax=ax)
    # scatter markers
    ax_scatter = pitch.formation(formation, positions=starting_xi.position_id, kind='scatter',
                                c='red', linewidth=3, s=350, xoffset=-8, ax=ax)
    
    # Add a title
    plt.title(f"{HOME}", fontsize=12, fontweight="bold", color="white")

    plt.show()

def get_away_formation(competition_id, season_id, home_team, away_team):
    """
    Generates and displays the formation of the away team at the start of a football match.

    Args:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    Returns:
        None: Displays the formation on a football pitch.

    Dependencies:
        Requires functions get_match_id, get_event_df, and get_tactics_df for data retrieval.
        Uses the VerticalPitch class for pitch visualization.

    Notes:
        This function fetches the starting XI and corresponding formation of the home team.
        It then visualizes the formation on a football pitch using the VerticalPitch class.

    Example:
        get_home_formation(competition_id=123, season_id=456, home_team='TeamA', away_team='TeamB')
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    event = get_event_df(away_team_id)
    tactics = get_tactics_df(away_team_id)

    AWAY = away_team

    starting_xi_event = event.loc[((event['type_name'] == 'Starting XI') &
                                (event['team_name'] == AWAY)), ['id', 'tactics_formation']]
    # joining on the team name and formation to the lineup
    starting_xi = tactics.merge(starting_xi_event, on='id')
    formation = starting_xi['tactics_formation'].iloc[0]

    pitch = VerticalPitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(6, 8.72))
    fig.patch.set_facecolor("#22312b")

    ax_text = pitch.formation(formation, positions=starting_xi.position_id, kind='text',
                            text=starting_xi.player_name.str.replace(' ', '\n'), c="white",
                            va='center', ha='center', fontsize=10, ax=ax)
    # scatter markers
    ax_scatter = pitch.formation(formation, positions=starting_xi.position_id, kind='scatter',
                                c='red', linewidth=3, s=350, xoffset=-8, ax=ax)
    
    # Add a title
    plt.title(f"{AWAY}", fontsize=12, fontweight="bold", color="white")

    plt.show()



