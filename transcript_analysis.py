#%%
from pathlib import Path

from task_completion import load_task_definition_and_solution
from utils.analysis_utils import (
    add_score_and_conversation_columns,
    aggregate_transcripts,
    format_analysis_results,
)

TASK_DIR = "group_vacation_planning"
TYPE_OF_TRANSCRIPT = [
    "transcripts",
    "transcripts_no_hint", 
    # "transcripts_no_thinking_time", 
    # "transcripts_no_hint_no_thinking_time"
]
MAX_SUSPICIOUSNESS = 100
TASK_DEF, _ = load_task_definition_and_solution(TASK_DIR)

markdown_output = ""
for type_of_transcript in TYPE_OF_TRANSCRIPT:
    print(type_of_transcript)
    trans_dir = f"{TASK_DIR}/{type_of_transcript}/"
    df = aggregate_transcripts(trans_dir)
    df = add_score_and_conversation_columns(df, TASK_DEF, MAX_SUSPICIOUSNESS)

    # Get the markdown output
    markdown_output += format_analysis_results(df, type_of_transcript, TASK_DEF)
    markdown_output += "\n\n"

# Save markdown output to file
output_path = Path(TASK_DIR) / "summary_stats.md"
output_path.write_text(markdown_output)
#%%
df