import streamlit as st
import mplsoccer
import pandas as pd
import matplotlib.pyplot as plt

import sys
import os
sys.path.insert(0, "css/")
sys.path.insert(1, "visualisations/")

from defensive_actions import * 
from get_formations import *
from gk_passes import *
from pass_maps import *
from pass_matrix import *
from pass_network import *
from passes_leading_to_shots import *
from cumulative_xg import *

# Page Configuration
#region  ----------------------------------------- #
page_config = st.set_page_config(page_title="SB Data Explorer", page_icon=":soccer:", #change 
                                 layout="centered", initial_sidebar_state="auto",
                                 menu_items={
                                        "Get Help": "mailto:remiawosanya8@gmail.com",
                                        "Report a bug": "mailto:remiawosanya8@gmail.com"
                                            })

# Load custom CSS
with open("css/custom.css", "r") as f:
    custom_css = f.read()

# Apply custom CSS using HTML
st.markdown(f'<style>{custom_css}</style>', unsafe_allow_html=True)
#endregion ---------------------------------------- #

# Title
#region  ----------------------------------------- #
_,title_column,_ = st.columns(spec = [1,1,1])

with title_column:
    title = st.title("**Statsbomb Data Explorer**", anchor=None)
#endregion ---------------------------------------- #

# Functions
#region  ----------------------------------------- #
@st.cache_data
def get_competition_ids():
    """
    Fetches a table of competition IDs for a specific season.

    This function uses the Sbopen parser to retrieve a table of competition data
    for a specific season (season_id = 27). It then filters out the "Champions League"
    competition from the table.

    Returns:
        pandas.DataFrame: A DataFrame containing competition IDs and related information.
    """
    parser = Sbopen()
    table = parser.competition()
    table = table[table["season_id"] == 27].reset_index(drop=True)
    table = table.loc[table["competition_name"] != "Champions League"]
    
    return table

@st.cache_data
def get_home_teams(season_id, competition_id):
    """
    Retrieves a list of home teams for a specific season and competition.

    Args:
        season_id (int): The ID of the season.
        competition_id (int): The ID of the competition.

    Returns:
        list: A list of unique home team names.
    """
    parser = Sbopen()
    match = parser.match(competition_id, season_id)

    home_teams = list(match["home_team_name"].unique())

    return home_teams

@st.cache_data
def get_away_teams(home_teams, season_id, competition_id):
    """
    Retrieves a list of away teams for a specific set of home teams, season, and competition.

    Args:
        home_teams (list): A list of home team names.
        season_id (int): The ID of the season.
        competition_id (int): The ID of the competition.

    Returns:
        list: A list of unique away team names.
    """
    parser = Sbopen()
    match = parser.match(competition_id, season_id)
    
    teams = {elem : pd.DataFrame() for elem in home_teams}
    for key in teams.keys():
        teams[key] = match[:][match["home_team_name"] == key] 

    # Combine matches for all home teams
    selected_home_team_matches = pd.concat(teams.values())

    unique_away_teams = selected_home_team_matches["away_team_name"].unique()
    return list(unique_away_teams)

@st.cache_data
def get_scoreline(competition_id, season_id, home_team, away_team):
                parser = Sbopen()
                match = parser.match(competition_id, season_id)

                unq = match["home_team_name"].unique()
                teams = {elem : pd.DataFrame() for elem in unq}

                for key in teams.keys():
                    teams[key] = match[:][match["home_team_name"] == key] 

                df = teams[home_team]

                # home score
                home_score = df[df["away_team_name"] == away_team]["home_score"].iloc[0]

                # away score
                away_score = df[df["away_team_name"] == away_team]["away_score"].iloc[0]

                text = f"{home_team} {home_score}:{away_score} {away_team}"
                return text

@st.cache_data
def get_goals_data(competition_id, season_id, home_team, away_team):
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    goals = get_event_df(away_team_id)
    goals_df = goals[goals["type_name"].isin(["Shot", "Own Goal Against"]) & 
    (goals["outcome_name"].isin(["Goal"]) | pd.isna(goals["outcome_name"]))].reset_index(drop=True)
    goals_df = goals_df[["period", "timestamp", "team_name", "player_name", 
                        "technique_name", "shot_statsbomb_xg"]] \
                        .rename(columns={
                            "period":"Period",
                            "timestamp":"Timestamp",
                            "team_name":"Team Name",
                            "player_name":"Player",
                            "technique_name":"Shot Technique",
                            "shot_statsbomb_xg":"xG"})
    
    # Add "Own Goal" column
    goals_df['Own Goal'] = goals_df.apply(lambda row: True if pd.isna(row['xG']) and pd.isna(row['Shot Technique']) else False, axis=1)
    return goals_df

@st.cache_data
def pass_network_df(competition_id, season_id, home_team, away_team, formation):
    """
    Generate a pass network DataFrame for a given match.
    
    Args:
        competition_id (int): ID of the competition.
        season_id (int): ID of the season.
        home_team (str): Name of the home team.
        away_team (str): Name of the away team.
        
    Returns:
        pandas.DataFrame: Pass network DataFrame.
    """
    away_team_id = get_match_id(competition_id, season_id, home_team, away_team)
    events = get_event_df(away_team_id)
    tactics = get_tactics_df(away_team_id)

    HOME = home_team
    FORMATION = formation

    events.loc[events["tactics_formation"].notnull(), "tactics_id"] = events.loc[
        events["tactics_formation"].notnull(), "id"]

    events[["tactics_id", "tactics_formation"]] = events.groupby("team_name")[[
        "tactics_id", "tactics_formation"]].ffill()

    events = events.loc[(events["team_name"] == HOME) & (events.tactics_formation == FORMATION)]

    ids = list(events["player_id"].unique())
    ids = [int(x) for x in ids if not np.isnan(x)]

    formation_dict = {1: "GK", 2: "RB", 3: "RCB", 4: "CB", 5: "LCB", 6: "LB", 7: "RWB",
                    8: "LWB", 9: "RDM", 10: "CDM", 11: "LDM", 12: "RM", 13: "RCM",
                    14: "CM", 15: "LCM", 16: "LM", 17: "RW", 18: "RAM", 19: "CAM",
                    20: "LAM", 21: "LW", 22: "RCF", 23: "ST", 24: "LCF", 25: "SS"}
    tactics["position_abbreviation"] = tactics["position_id"].map(formation_dict)
    
    tact_ids = list(tactics["player_id"].unique())
    tact_ids = [x for x in tact_ids if x in ids]
    tactics = tactics.loc[tactics["player_id"].isin(tact_ids)][["position_abbreviation", "player_name", "jersey_number"]]
    tactics_df = tactics.drop_duplicates(subset=["jersey_number"], keep="first")
    tactics_df = tactics_df.set_index("jersey_number")

    return tactics_df
#endregion ---------------------------------------- #

# Sidebar Content
#region  ----------------------------------------- #
season_id = 27
comp_table_ids = get_competition_ids()

st.sidebar.image("https://raw.githubusercontent.com/statsbomb/logos/main/StatsBombPython_Lock.svg", use_column_width=True)
st.sidebar.success("Select a League & Home Team of interest and see how they performed against the selected Away Team")

league_options = list(comp_table_ids["competition_name"].unique())
league_selector = st.sidebar.radio(label="League:", options=league_options)

selected_competition_row = comp_table_ids[comp_table_ids["competition_name"] == league_selector]
selected_competition_id = selected_competition_row["competition_id"].iloc[0]

home_teams = get_home_teams(season_id, selected_competition_id)
home_options = home_teams

away_teams = get_away_teams(home_teams, season_id, selected_competition_id)
away_options = away_teams

home_selector = st.sidebar.selectbox(label="Home Team:", options=home_options)
# remove the selected home_team from the list of away_teams
if home_selector in away_options:
    away_options.remove(home_selector)

away_selector = st.sidebar.selectbox(label="Away Team:", options=away_options)

vis_options = ["Starting XIs", "Cumulative xG", "Player Defensive Actions", "GK Passing Distribution", 
               "Player Pass Maps", "Pass Matrix", "Pass Network", "Passes Leading to Shots"]
visualisation_options = st.sidebar.selectbox(label="Visual:", options=vis_options)

selected_visualisation = None

if visualisation_options == "Starting XIs":
    teams = st.sidebar.radio(label="Home/Away", options=["Home", "Away"])
    if teams == "Home":
        h_starting = get_home_formation(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
    if teams == "Away":
        a_starting = get_away_formation(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
elif visualisation_options == "Pass Matrix":
    matrix = pass_matrix(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
elif visualisation_options == "Cumulative xG":
    selected_visualisation = cumulative_xg(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
elif visualisation_options == "Player Defensive Actions":
    players = player_list(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)[1]
    player_select = st.sidebar.selectbox(label="Player:", options=players)
    if player_select:
        selected_visualization = defensive_actions(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector, player=player_select)
elif visualisation_options == "GK Passing Distribution":
    selected_visualisation = gk_passmap(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
elif visualisation_options == "Player Pass Maps":
    selected_visualisation = team_pass_maps(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
elif visualisation_options == "Pass Network":
    formations = get_formations(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
    formation_select = st.sidebar.selectbox(label="Formation:", options=formations)
    if formation_select:
        selected_visualisation = pass_network(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector, formation=formation_select)
elif visualisation_options == "Passes Leading to Shots":
    selected_visualisation = passes_leading_to_shots(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)    

# Add a button to trigger the page update
update_button = st.sidebar.button("Apply Filters")
#endregion ---------------------------------------- #
    
# Text & Links
#region  ----------------------------------------- #
text = """
The purpose of this application is to provide users a way to easily and quickly visualise football data from Statsbomb.
The project comes on the back of Statsbomb releasing data from the big 5 leagues for the 15/16 season.
\n**Note:** This application looks at match performances of some selected home team vs the selected away team.
Use the sidebar to filter page content.
"""

linkedin = "https://www.linkedin.com/in/remi-awosanya-686b97191/"
medium = "https://medium.com/@remiawosanya8"
#endregion ---------------------------------------- #

# Page Content
#region  ----------------------------------------- #
tab1, tab2 = st.tabs(["Home Page", "Match Data"])

with tab1:
    st.caption("Created by Remi Awosanya")
    st.header("Welcome!")
    st.write(text)
    
    # Competitions Table
    #region  ----------------------------------------- #
    def get_competition_table():
        """
        Fetches a table of available competition IDs.

        This function uses the Sbopen parser to retrieve a table of competition data. 

        Returns:
            pandas.DataFrame: A DataFrame containing competition IDs and related information.
        """
        parser = Sbopen()
        table = parser.competition()
        
        return table
    
    comp_table = get_competition_table()
    st.markdown('<span style="font-size:30px; color:red">Statsbomb</span> Competitions', unsafe_allow_html=True)
    st.dataframe(comp_table)
    #endregion ---------------------------------------- #
    
    with st.container():
        st.markdown(f"You can find me: [LinkedIn]({linkedin}) | [Medium]({medium})")


with tab2:  
    # Tab Content
    #region  ----------------------------------------- #
    if update_button:
        with st.spinner(text="Updating..."):   
            scoreline = get_scoreline(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
            sl = st.header(scoreline, anchor=None)

        if visualisation_options == "Pass Matrix":
            def render_dataframe(dataframe):
                # Convert the DataFrame to HTML
                dataframe_html = dataframe.to_html(classes='data', index=False, border=0)

                # Add CSS styling to the DataFrame
                styled_html = f"<style>" \
                            f"table.dataframe {{border-collapse: collapse; width: 20%; margin: auto;}}" \
                            f"table.dataframe td, table.dataframe th {{border: 1px solid black; padding: 8px; margin: 0;}}" \
                            f"</style>{dataframe_html}"

                return styled_html

            st.markdown(render_dataframe(matrix), unsafe_allow_html=True)
        
        if visualisation_options == "Passes Leading to Shots":
            goals_dataframe = get_goals_data(selected_competition_id, season_id, home_team=home_selector, away_team=away_selector)
            goals = st.dataframe(goals_dataframe)
            passes_leading_shots = st.pyplot(selected_visualisation)

        else:
            sv = st.pyplot(selected_visualisation)
            st.set_option("deprecation.showPyplotGlobalUse", False)

    else:
        st.success("Select a fixture in the sidebar, don't forget to click Apply Filters!")
    #endregion ---------------------------------------- #
#endregion ---------------------------------------- #

