import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cmasher as cmr
from PIL import Image
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
from get_lineup_df import get_lineup_df

def team_pass_maps(competition_id, season_id, home_team, away_team):
    """
    Generate pass maps for players in a football match.

    Parameters:
        competition_id (int): The ID of the competition.
        season_id (int): The ID of the season.
        home_team (str): The name of the home team.
        away_team (str): The name of the away team.

    This function generates pass maps for players in a football match. It retrieves event, tactic, and lineup data,
    filters and processes the data, and plots pass maps for each player. It also includes information about substitutions,
    pass outcomes, and pass success rates.

    Example:
        team_pass_maps(123, 2022, "Team A", "Team B")
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    events = get_event_df(away_team_id)
    tactics = get_tactics_df(away_team_id)
    lineup = get_lineup_df(away_team_id)

    # dataframe with player_id and when they were subbed off
    time_off = events.loc[(events["type_name"] == "Substitution"), ["player_id", "minute"]]
    time_off.rename({"minute": "off"}, axis="columns", inplace=True)

    # dataframe with player_id and when they were subbed on
    time_on = events.loc[(events["type_name"] == "Substitution"), ["substitution_replacement_id", "minute"]]
    time_on.rename({"substitution_replacement_id": "player_id",
                    "minute": "on"}, axis="columns", inplace=True)
    players_on = time_on["player_id"]

    # merge on times subbed on/off
    lineup = lineup.merge(time_on, on="player_id", how="left")
    lineup = lineup.merge(time_off, on="player_id", how="left")

    # filter the tactics lineup for the starting xi
    starting_ids = events[events["type_name"] == "Starting XI"].id
    starting_xi = tactics[tactics["id"].isin(starting_ids)]
    starting_players = starting_xi["player_id"]

    # filter the lineup for players that actually played
    mask_played = ((lineup["on"].notnull()) | (lineup["off"].notnull()) |
                (lineup["player_id"].isin(starting_players)))
    lineup = lineup[mask_played].copy()

    # get the first position for each player and add this to the lineup dataframe
    player_positions = (events[["player_id", "position_id"]]
                        .dropna(how="any", axis="rows")
                        .drop_duplicates("player_id", keep="first"))
    lineup = lineup.merge(player_positions, how="left", on="player_id")

    # add on the position abbreviation
    formation_dict = {1: "GK", 2: "RB", 3: "RCB", 4: "CB", 5: "LCB", 6: "LB", 7: "RWB",
                    8: "LWB", 9: "RDM", 10: "CDM", 11: "LDM", 12: "RM", 13: "RCM",
                    14: "CM", 15: "LCM", 16: "LM", 17: "RW", 18: "RAM", 19: "CAM",
                    20: "LAM", 21: "LW", 22: "RCF", 23: "ST", 24: "LCF", 25: "SS"}
    lineup["position_abbreviation"] = lineup["position_id"].map(formation_dict)

    # sort the dataframe so the players are
    # in the order of their position (if started), otherwise in the order they came on
    lineup["start"] = lineup["player_id"].isin(starting_players)
    lineup.sort_values(["team_name", "start", "on", "position_id"],
                    ascending=[True, False, True, True], inplace=True)

    # filter the lineup for home_team
    lineup_team = lineup[lineup["team_name"] == home_team].copy()

    # filter the events to exclude some set pieces
    set_pieces = ["Throw-in", "Free Kick", "Corner", "Kick Off", "Goal Kick"]

    # for the team pass map
    pass_receipts = events[(events["team_name"] == home_team) & (events["type_name"] == "Ball Receipt")].copy()

    # for the player pass maps
    passes_excl_throw = events[(events["team_name"] == home_team) & (events["type_name"] == "Pass") &
                            (events["sub_type_name"] != "Throw-in")].copy()

    # identify how many players played and how many subs were used
    num_players = len(lineup_team)
    num_sub = num_players - 11

    # add padding to the top so we can plot the titles, and raise the pitch lines
    pitch = Pitch(pad_top=10, line_zorder=2)

    # arrow properties for the sub on/off
    green_arrow = dict(arrowstyle="simple, head_width=0.7",
                    connectionstyle="arc3,rad=-0.8", fc="green", ec="green")
    red_arrow = dict(arrowstyle="simple, head_width=0.7",
                    connectionstyle="arc3,rad=-0.8", fc="red", ec="red")

    # filtering out some highlight_text warnings - the warnings aren't correct as the
    # text fits inside the axes.
    warnings.simplefilter("ignore", UserWarning)

    # plot the 5 * 3 grid
    fig, axs = pitch.grid(nrows=5, ncols=3, figheight=30,
                        endnote_height=0.03, endnote_space=0,
                        axis=False,
                        title_height=0.08, grid_height=0.84)

    # cycle through the grid axes and plot the player pass maps
    for idx, ax in enumerate(axs["pitch"].flat):
        # only plot the pass maps up to the total number of players
        if idx < num_players:
            # filter the complete/incomplete passes for each player (excudes throw-ins)
            lineup_player = lineup_team.iloc[idx]
            player_id = lineup_player["player_id"]
            player_pass = passes_excl_throw[passes_excl_throw["player_id"] == player_id]
            complete_pass = player_pass[player_pass["outcome_name"].isnull()]
            incomplete_pass = player_pass[player_pass["outcome_name"].notnull()]

            # plot the arrows
            pitch.arrows(complete_pass["x"], complete_pass["y"],
                        complete_pass["end_x"], complete_pass["end_y"],
                        color="#56ae6c", width=2, headwidth=4, headlength=6, ax=ax)
            pitch.arrows(incomplete_pass["x"], incomplete_pass["y"],
                        incomplete_pass["end_x"], incomplete_pass["end_y"],
                        color="#7065bb", width=2, headwidth=4, headlength=6, ax=ax)

            # plot the title for each player axis
            total_pass = len(complete_pass) + len(incomplete_pass)
            annotation_string = (f'{lineup_player["position_abbreviation"]} | '
                                f'{lineup_player["player_nickname"]} | '
                                f'<{len(complete_pass)}>/{total_pass} | '
                                f'{round(100 * len(complete_pass)/total_pass, 1)}%')
            ax_text(0, -5, annotation_string, ha="left", va="center", fontsize=20,
                    highlight_textprops=[{"color": "#56ae6c"}], ax=ax)

            # add information for subsitutions on/off and arrows
            if not np.isnan(lineup_team.iloc[idx].off):
                ax.text(116, -10, str(lineup_team.iloc[idx].off.astype(int)), fontsize=20,
                        ha="center", va="center")
                ax.annotate("", (120, -2), (112, -2), arrowprops=red_arrow)
            if not np.isnan(lineup_team.iloc[idx].on):
                ax.text(104, -10, str(lineup_team.iloc[idx].on.astype(int)), fontsize=20,
                        ha="center", va="center")
                ax.annotate("", (108, -2), (100, -2), arrowprops=green_arrow)

    # plot on the last Pass Map
    pitch.kdeplot(x=pass_receipts["x"], y=pass_receipts["y"], ax=ax,
                cmap=cmr.lavender,
                levels=100,
                thresh=0, fill=True)
    ax.text(0, -5, "Pass Receipt Heatmap", ha="left", va="center",
            fontsize=20)

    # remove unused axes (if any)
    for ax in axs["pitch"].flat[11 + num_sub:-1]:
        ax.remove()

    SB_LOGO_URL = ('https://raw.githubusercontent.com/statsbomb/open-data/'
                'master/img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png')

    sb_logo = Image.open(urlopen(SB_LOGO_URL))
    ax_sb_logo = add_image(sb_logo, fig, left=0.701126,
                        # set the bottom and height to align with the endnote
                        bottom=axs["endnote"].get_position().y0,
                        height=axs["endnote"].get_position().height)

    # title text
    axs["title"].text(0.5, 0.65, f'{home_team} Pass Maps', fontsize=40,
                    va="center", ha="center")
    SUB_TEXT = ("Successful = Green | Unsuccessful = Blue\n"
                "Team heatmap includes all attempted pass receipts")
    axs["title"].text(0.5, 0.35, SUB_TEXT, fontsize=20, va="center", ha="center")

    #plt.savefig(f"{home_team} Pass Maps vs {away_team}")
    plt.show()







