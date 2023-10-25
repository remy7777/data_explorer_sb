from mplsoccer import Sbopen
import pandas as pd

def get_event_df(away_team_id):
    parser = Sbopen()
    event = parser.event(away_team_id)[0]

    return event





