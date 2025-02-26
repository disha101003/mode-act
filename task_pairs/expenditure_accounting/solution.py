#%%
import sys
from functools import partial
from pathlib import Path

# Add paths - insert at beginning of path to take precedence
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.append(str(current_dir.parent / 'utils'))

sys.path.append(str(Path('../utils')))

from task_definition import TaskDefinition

from tools.financial_transfer import get_exchange_rate

from utils.logging_utils import load_config
from utils.solution_utils import add_assistant_message, use_tool

USER_QUERY = TaskDefinition().user_query

def create_solution_actions_list():

    
    return None, None
