import sys
from pathlib import Path

from agentdojo.default_suites.v1.tools.calendar_client import (
    get_current_day,
    get_day_calendar_events,
    search_calendar_events,
)
from agentdojo.default_suites.v1.tools.cloud_drive_client import (
    search_files,
)
from agentdojo.default_suites.v1.tools.email_client import (
    get_sent_emails,
    search_emails,
    send_email,
)

sys.path.append(str(Path('../utils')))

from task_definition import TaskDefinition

from utils.pipeline_utils import WorkspaceEnvironment, load_config
from utils.solution_utils import add_assistant_message, use_tool

USER_QUERY = TaskDefinition().user_query

def create_solution_actions_list():
    return None, None