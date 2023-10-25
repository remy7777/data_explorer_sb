import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from urllib.request import urlopen
from mplsoccer import Sbopen, Pitch, add_image
from highlight_text import ax_text
import warnings
warnings.filterwarnings("ignore")
import sys

sys.path.insert(0, "functions/")
from get_match_id import get_match_id
from get_event_df import get_event_df
from get_tactics_df import get_tactics_df

def get_formations(competition_id, season_id, home_team, away_team):
    """
    Retrieve the unique formations used by the specified home team.

    Args:
        away_team_id (int): The ID of the away team.
        home_team (str): The name of the home team.

    Returns:
        list: A list of unique formations used by the specified home team.
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    events = get_event_df(away_team_id)
    events.loc[events["tactics_formation"].notnull(), "tactics_id"] = events.loc[
    events["tactics_formation"].notnull(), "id"]

    events[["tactics_id", "tactics_formation"]] = events.groupby("team_name")[[
    "tactics_id", "tactics_formation"]].ffill()
    events["tactics_formation"] = events["tactics_formation"].astype("int").astype("str")
    grouped = events.groupby("team_name").tactics_formation.unique()
    home_formation = list(grouped[home_team])

    return home_formation

def pass_network(competition_id, season_id, home_team, away_team, formation):
    """
    Generate a pass network visualization for a given match.

    Args:
        competition_id (int): ID of the competition.
        season_id (int): ID of the season.
        home_team (str): Name of the home team.
        away_team (str): Name of the away team.
        formation (str): Formation code.

    Returns:
        Pass Network
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    events = get_event_df(away_team_id)
    tactics = get_tactics_df(away_team_id)

    TEAM = home_team

    events.loc[events["tactics_formation"].notnull(), "tactics_id"] = events.loc[
        events["tactics_formation"].notnull(), "id"]

    events[["tactics_id", "tactics_formation"]] = events.groupby("team_name")[[
        "tactics_id", "tactics_formation"]].ffill()

    formation_dict = {1: "GK", 2: "RB", 3: "RCB", 4: "CB", 5: "LCB", 6: "LB", 7: "RWB",
                    8: "LWB", 9: "RDM", 10: "CDM", 11: "LDM", 12: "RM", 13: "RCM",
                    14: "CM", 15: "LCM", 16: "LM", 17: "RW", 18: "RAM", 19: "CAM",
                    20: "LAM", 21: "LW", 22: "RCF", 23: "ST", 24: "LCF", 25: "SS"}
    tactics["position_abbreviation"] = tactics["position_id"].map(formation_dict)

    sub = events.loc[events["type_name"] == "Substitution",
                    ["tactics_id", "player_id", "substitution_replacement_id",
                    "substitution_replacement_name"]]

    players_sub = tactics.merge(sub.rename({"tactics_id": "id"}, axis="columns"),
                                on=["id", "player_id"], how="inner", validate="1:1")
    players_sub = (players_sub[["id", "substitution_replacement_id", "position_abbreviation"]]
                .rename({"substitution_replacement_id": "player_id"}, axis="columns"))

    tactics = pd.concat([tactics, players_sub])
    tactics.rename({"id": "tactics_id"}, axis="columns", inplace=True)
    tactics = tactics[["tactics_id", "player_id", "position_abbreviation"]]

    # add on the position the player was playing in the formation to the events dataframe
    events = events.merge(tactics, on=["tactics_id", "player_id"], how="left", validate="m:1")

    # add on the position the receipient was playing in the formation to the events dataframe
    events = events.merge(tactics.rename({"player_id": "pass_recipient_id"},
                                        axis="columns"), on=["tactics_id", "pass_recipient_id"],
                        how="left", validate="m:1", suffixes=["", "_receipt"])
    
    events["tactics_formation"] = events["tactics_formation"].astype("int").astype("str")
    FORMATION = formation

    pass_cols = ["id", "position_abbreviation", "position_abbreviation_receipt"]
    passes_formation = events.loc[(events.team_name == TEAM) & (events.type_name == "Pass") &
                                (events.tactics_formation == formation) &
                                (events.position_abbreviation_receipt.notnull()), pass_cols].copy()

    location_cols = ["position_abbreviation", "x", "y"]
    location_formation = events.loc[(events.team_name == TEAM) &
                                    (events.type_name.isin(["Pass", "Ball Receipt"])) &
                                    (events.tactics_formation == FORMATION), location_cols].copy()

    # average locations
    average_locs_and_count = (location_formation.groupby("position_abbreviation")
                            .agg({"x": ["mean"], "y": ["mean", "count"]}))
    average_locs_and_count.columns = ["x", "y", "count"]

    # calculate the number of passes between each position (using min/ max so we get passes both ways)
    passes_formation["pos_max"] = (passes_formation[["position_abbreviation",
                                                    "position_abbreviation_receipt"]]
                                .max(axis="columns"))
    passes_formation["pos_min"] = (passes_formation[["position_abbreviation",
                                                    "position_abbreviation_receipt"]]
                                .min(axis="columns"))
    passes_between = passes_formation.groupby(["pos_min", "pos_max"]).id.count().reset_index()
    passes_between.rename({"id": "pass_count"}, axis="columns", inplace=True)

    # add on the location of each player so we have the start and end positions of the lines
    passes_between = passes_between.merge(average_locs_and_count, left_on="pos_min", right_index=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on="pos_max", right_index=True,
                                        suffixes=["", "_end"])

    MAX_LINE_WIDTH = 18
    MAX_MARKER_SIZE = 3000
    passes_between["width"] = (passes_between.pass_count / passes_between.pass_count.max() *
                            MAX_LINE_WIDTH)
    average_locs_and_count["marker_size"] = (average_locs_and_count["count"]
                                            / average_locs_and_count["count"].max() * MAX_MARKER_SIZE)

    MIN_TRANSPARENCY = 0.3
    color = np.array(to_rgba("white"))
    color = np.tile(color, (len(passes_between), 1))
    c_transparency = passes_between.pass_count / passes_between.pass_count.max()
    c_transparency = (c_transparency * (1 - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
    color[:, 3] = c_transparency

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#22312b", line_color="#c7d5cc")
    fig, axs = pitch.grid(figheight=10, title_height=0.08, endnote_space=0,
                        axis=False,
                        title_space=0, grid_height=0.82, endnote_height=0.05)
    fig.set_facecolor("#22312b")
    pass_lines = pitch.lines(passes_between.x, passes_between.y,
                            passes_between.x_end, passes_between.y_end, lw=passes_between.width,
                            color=color, zorder=1, ax=axs["pitch"])
    pass_nodes = pitch.scatter(average_locs_and_count.x, average_locs_and_count.y,
                            s=average_locs_and_count.marker_size,
                            color="red", edgecolors="black", linewidth=1, alpha=1, ax=axs["pitch"])
    for index, row in average_locs_and_count.iterrows():
        pitch.annotate(row.name, xy=(row.x, row.y), c="white", va="center",
                    ha="center", size=16, weight="bold", ax=axs["pitch"])

    # endnote /title
    TITLE_TEXT = f"{TEAM} Pass Network"
    axs["title"].text(0.5, 0.7, TITLE_TEXT, color="#c7d5cc",
                    va="center", ha="center", fontsize=30)
    axs["title"].text(0.5, 0.25, f"{FORMATION}", color="#c7d5cc",
                    va="center", ha="center", fontsize=18)

    #plt.savefig("pass_network")
    plt.show()


