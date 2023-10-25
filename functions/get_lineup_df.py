from mplsoccer import Sbopen
import pandas as pd

def get_lineup_df(away_team_id):
    parser = Sbopen()
    lineup = parser.lineup(away_team_id)

    return lineup
