from mplsoccer import Sbopen
import pandas as pd

def get_match_id(competition_id, season_id, home_team, away_team):
    parser = Sbopen()
    match = parser.match(competition_id, season_id)

    unq = match["home_team_name"].unique()
    teams = {elem : pd.DataFrame() for elem in unq}

    for key in teams.keys():
        teams[key] = match[:][match["home_team_name"] == key] 

    df = teams[home_team]
    away_team_id = df[df["away_team_name"] == away_team]["match_id"].item()

    return away_team_id



    

# match_ids = get_match_ids(competition_id=2, season_id=27, team="Chelsea")
# away_team = match_ids[match_ids["away_team_name"] == "Arsenal"]["match_id"].item()








