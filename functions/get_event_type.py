from mplsoccer import Sbopen
import pandas as pd
import sys

sys.path.insert(0, "functions/")
from get_event_df import get_event_df
  
def get_event_type(away_team_id, event):
    fix = get_event_df(away_team_id)
    fix_event = fix.loc[fix["type_name"] == event]
    fix_event = fix_event.dropna(axis=1)

    return fix_event
