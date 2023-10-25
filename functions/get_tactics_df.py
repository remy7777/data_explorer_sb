from mplsoccer import Sbopen
import pandas as pd

def get_tactics_df(away_team_id): 
    parser = Sbopen()   
    tactics = parser.event(away_team_id)[3]

    return tactics
