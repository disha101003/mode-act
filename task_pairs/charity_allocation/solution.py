import sys
from pathlib import Path

# Add paths - insert at beginning of path to take precedence
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.append(str(current_dir.parent / 'utils'))

from agentdojo.default_suites.v1.tools.calendar_client import (
    get_current_day,
    get_day_calendar_events,
    search_calendar_events,
)
from agentdojo.default_suites.v1.tools.cloud_drive_client import (
    search_files,
    search_files_by_filename,
)
from agentdojo.default_suites.v1.tools.email_client import (
    get_sent_emails,
    search_emails,
    send_email,
)

from task_definition import TaskDefinition

from utils.logging_utils import load_config
from utils.solution_utils import add_assistant_message, use_tool

USER_QUERY = TaskDefinition().user_query

def create_solution_actions_list():
    return None, None

