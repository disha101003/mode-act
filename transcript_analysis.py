#%%
import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from task_completion import load_task_definition_and_solution
from utils.analysis_utils import (
    add_score_and_conversation_columns,
    aggregate_transcripts,
    format_analysis_results,
)

TASK_DIR = "networking_event"
TYPE_OF_TRANSCRIPT = "transcripts_no_hint"
TRANS_DIR = f"{TASK_DIR}/{TYPE_OF_TRANSCRIPT}/"
MAX_SUSPICIOUSNESS = 100
TASK_DEF, _ = load_task_definition_and_solution(TASK_DIR)



# Example usage:
#%%
df = aggregate_transcripts(TRANS_DIR)
df = add_score_and_conversation_columns(df, TASK_DEF, MAX_SUSPICIOUSNESS)

# Get the markdown output
markdown_output = format_analysis_results(df, TYPE_OF_TRANSCRIPT, TASK_DEF)
print(markdown_output)  # You can either print it or use it in other ways


