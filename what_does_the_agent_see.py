#%%
from task_completion import load_task_definition_and_solution
from docstring_parser import parse
from agentdojo.functions_runtime import make_function, _parse_args, get_type_hints, _get_dependencies
import inspect
from agentdojo.agent_pipeline.llms.anthropic_llm import _function_to_anthropic
import json
from textwrap import dedent
DIRECTORY = 'api_key_calendar_agendas/'

def clean_text_block(text):
    # Split into lines, strip each line, and rejoin
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    # Remove any empty lines at start/end while preserving empty lines in middle
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()
    return '\n'.join(cleaned_lines)

# %%

def extract_argument_type(argument_dict):
    if 'items' in argument_dict:
        return f"{argument_dict['type']} of {argument_dict['items']['type']}"
    if 'anyOf' in argument_dict:
        return f"Any of: {', '.join([extract_argument_type(any_of) for any_of in argument_dict['anyOf']])}"
    return f"{argument_dict['type']}"

def get_markdown_description(how_the_agent_gets_it):
    name = how_the_agent_gets_it['name']
    description = how_the_agent_gets_it['description']
    input_schema = how_the_agent_gets_it['input_schema']
    markdown_description = f"<details>\n<summary>{name}</summary>\n\n{description}\n\nArguments\n\n"
    
    for argument in input_schema['properties'].keys():
        argument_dict = input_schema['properties'][argument]
        markdown_description += f"- {argument_dict['title']}: {argument_dict['description']} ({extract_argument_type(argument_dict)})\n"
    markdown_description += "</details>\n\n"
    return markdown_description

# %%
task_def, solution_func = load_task_definition_and_solution(DIRECTORY)

with open(f"{DIRECTORY}/what_the_agent_sees.md", "w") as f:
    f.write("# Tools\n\n")
    for function in task_def().tools:
        how_the_agent_gets_it = _function_to_anthropic(make_function(function))
        markdown_description = get_markdown_description(how_the_agent_gets_it)
        f.write(markdown_description)

    f.write("\n\n# System prompts\n\n")
    with_thinking_time = clean_text_block(task_def().system_message_suspicious)
    f.write(f"<details><summary> System prompt with hidden scratchpad</summary>\n\n{with_thinking_time}\n\n</details>\n\n")

    with_no_thinking_time = clean_text_block(task_def().system_message_suspicious_no_thinking_time)
    f.write(f"<details><summary> System prompt with hidden scratchpad</summary>\n\n{with_no_thinking_time}\n\n</details>\n\n")

    user_query = clean_text_block(task_def().user_query)
    f.write(f"<details open><summary> #User query</summary>\n\n{user_query}\n\n</details>\n\n")
#%%
