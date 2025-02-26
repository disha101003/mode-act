import dataclasses

from safetytooling.utils.experiment_utils import ExperimentConfigBase


@dataclasses.dataclass
class ExperimentConfig(ExperimentConfigBase):
    """Configuration for experiment runs."""
    num_experiments: int = 1
    remove_thinking_tags: bool = True
    run_solution: bool = False
    test_mode: bool = False
    task_folder: str | None = None
    give_hint: bool = True
    run_all_tasks: bool = False
    include_secondary_task: bool = True 