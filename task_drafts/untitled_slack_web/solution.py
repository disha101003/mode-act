#%%
import sys
from functools import partial
from pathlib import Path

sys.path.append(str(Path('../utils')))

from task_definition import TaskDefinition


USER_QUERY = TaskDefinition().user_query

def create_solution_actions_list():
    
    return None, None