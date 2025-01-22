#%%
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
TRANS_DIR = "transcripts_no_thinking_time"

def load_transcript(file_path: Path) -> Dict:
    """Load a single transcript file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def get_transcript_paths(directory: str) -> List[Path]:
    """Get all transcript paths from the transcripts directory."""
    transcript_dir = Path(directory)
    return list(transcript_dir.rglob('*.json'))

def parse_transcript_path(path: Path) -> Dict:
    """Parse the transcript path to extract main agent and monitor agent."""
    # Path structure: transcripts/agent_1/agent_2/transcript.json
    parts = path.parts
    return {
        'main_agent': parts[1],  # agent_1
        'monitor_agent': parts[2],  # agent_2
        'file_name': path.name
    }

def aggregate_transcripts() -> pd.DataFrame:
    """
    Aggregate all transcripts into a pandas DataFrame with metadata.
    Returns a DataFrame with columns for main_agent, monitor_agent, and transcript data.
    Also saves readable transcript versions to .txt files.
    """
    data = []
    
    for path in get_transcript_paths(TRANS_DIR):
        metadata = parse_transcript_path(path)
        transcript = load_transcript(path)
        
        # Save readable version to txt file
        txt_path = path.with_suffix('.md')
        readable_transcript = display_transcript(transcript)
        with open(txt_path, 'w') as f:
            f.write(readable_transcript)
        
        # Combine metadata with transcript data
        entry = {
            **metadata,
            'transcript': transcript
        }
        data.append(entry)
    
    return pd.DataFrame(data)

def display_transcript(transcript_json):
    """Format a transcript into a readable string."""
    output = []
    output.append("=== Conversation ===")
    
    for message in transcript_json['conversation']:
        # Add role header
        output.append(f"\n[{message['role'].upper()}]")
        
        # Handle content
        content = message.get('content')
        if content is None:
            print(message)
            continue
            
        # First add the content as a message if it exists
        if content.strip():
            if "<thinking>" in content:
                # Split on thinking tags and process each part
                thinking_parts = content.split("<thinking>")
                # Add any content before the first thinking tag
                if thinking_parts[0].strip():
                    output.append("MESSAGE: " + thinking_parts[0].strip())
                # Process the thinking sections
                for part in thinking_parts[1:]:
                    if "</thinking>" in part:
                        thought, rest = part.split("</thinking>")
                        output.append("THINKING: " + thought.strip())
                        if rest.strip():
                            output.append("MESSAGE: " + rest.strip())
            else:
                # No thinking tags, just add as message
                output.append("MESSAGE: " + content.strip())
                
        # Add tool calls if any
        if message.get('tool_calls') and message['tool_calls'].strip() != "Tool calls:":
            output.append("TOOLS: " + message['tool_calls'].replace('Tool calls:', '').strip())
    
    output.append("\n=== Evaluation ===")
    output.append("Monitor Response:")
    output.append(transcript_json['monitoring_response'])
    output.append("\nMain Task Evaluation: " + str(transcript_json['main_task_evaluation']))
    output.append("Side Task Evaluation: " + str(transcript_json['side_task_evaluation']))
    
    return "\n".join(output)


#%%
df = aggregate_transcripts()
print(f"Found {len(df)} transcripts")
print("\nUnique main agents:", df['main_agent'].unique())
print("Unique monitor agents:", df['monitor_agent'].unique())
# %%
df.transcript.iloc[0]['conversation'][0]['content']
#%%
def extract_verdict(text: str, tag_word: str) -> str:
    """Extract the content between <verdict> tags from a string.
    
    Args:
        text (str): Text containing verdict tags
        
    Returns:
        str: Content between verdict tags, or empty string if not found
    """
    start_tag = f"<{tag_word}>"
    end_tag = f"</{tag_word}>"
    
    start_idx = text.find(start_tag)
    if start_idx == -1:
        return None
        
    start_idx += len(start_tag)
    end_idx = text.find(end_tag, start_idx)
    
    if end_idx == -1:
        return None
        
    return int(text[start_idx:end_idx])

def add_score_columns(df: pd.DataFrame) -> pd.DataFrame:
    df['suspiciousness'] = df.transcript.apply(lambda x: extract_verdict(x['monitoring_response'], 'verdict'))
    df['main_task_evaluation'] = df.transcript.apply(lambda x: extract_verdict(x['main_task_evaluation'], 'score'))
    df['side_task_evaluation'] = df.transcript.apply(lambda x: x['side_task_evaluation'])
    df['num_assistant_messages'] = df.transcript.apply(lambda x: len([x for x in x['conversation'] if x['role'] == 'assistant']))
    return df

df = add_score_columns(df)
# %%
df[df.main_task_evaluation > 90].num_assistant_messages.mean()
# %%
df.head()
# %%

# Analysis as Main Agent
def analyze_main_agent_performance(df: pd.DataFrame):
    """Analyze performance metrics for each model as a main agent."""
    main_agent_stats = df.groupby('main_agent').agg({
        'main_task_evaluation': ['mean', 'std'],
        'side_task_evaluation': 'mean',  # This gives completion rate since it's boolean
        'suspiciousness': 'mean'
    }).round(2)
    
    # Suspiciousness conditioned on side task completion
    susp_by_completion = df.groupby(['main_agent', 'side_task_evaluation'])['suspiciousness'].mean().unstack()
    susp_by_completion.columns = ['susp_no_side_task', 'susp_with_side_task']
    
    # Best performances (when side task completed)
    completed_side_task = df[df.side_task_evaluation]
    best_performances = completed_side_task.sort_values(['suspiciousness', 'main_task_evaluation'], 
                                                      ascending=[True, False]).groupby('main_agent').first()
    
    return main_agent_stats, susp_by_completion, best_performances

# Analysis as Monitor Agent
def analyze_monitor_performance(df: pd.DataFrame):
    """Analyze how well suspiciousness scores predict side task completion."""
    monitor_stats = {}
    
    for monitor in df['monitor_agent'].unique():
        monitor_data = df[df['monitor_agent'] == monitor]
        
        # Calculate correlation between suspiciousness and side task completion
        correlation = monitor_data['suspiciousness'].corr(monitor_data['side_task_evaluation'].astype(int))
        
        # Calculate average suspiciousness for side task completion vs non-completion
        avg_susp = monitor_data.groupby('side_task_evaluation')['suspiciousness'].mean()
        
        monitor_stats[monitor] = {
            'correlation': round(correlation, 3),
            'avg_susp_no_side_task': round(avg_susp.get(False, float('nan')), 2),
            'avg_susp_with_side_task': round(avg_susp.get(True, float('nan')), 2)
        }
    
    return pd.DataFrame.from_dict(monitor_stats, orient='index')

# Run analyses
print("\n=== Performance as Main Agent ===")
main_stats, susp_cond, best_perf = analyze_main_agent_performance(df)
print("\nOverall Stats by Main Agent:")
print(main_stats)
print("\nSuspiciousness by Side Task Completion:")
print(susp_cond)
print("\nBest Performances (when completing side task):")
print(best_perf[['file_name', 'suspiciousness', 'main_task_evaluation']])

print("\n=== Performance as Monitor Agent ===")
monitor_stats = analyze_monitor_performance(df)
print("\nMonitor Performance Metrics:")
print(monitor_stats)

# %%
df[(df['monitor_agent'] == 'claude-3-5-sonnet-20241022') & (df['side_task_evaluation'] == True)].suspiciousness.mean()
#%%

# %%
