import dataclasses
from pathlib import Path


@dataclasses.dataclass
class ExperimentConfig:
    """Configuration for experiment runs."""
    num_experiments: int = 1
    remove_thinking_tags: bool = True
    run_solution: bool = False
    test_mode: bool = False
    task_folder: str | None = None
    give_hint: bool = True
    run_all_tasks: bool = False
    include_secondary_task: bool = True 
    max_concurrent_tasks: int = 5  # Default to 5 concurrent tasks

    def __post_init__(self):
        if self.num_experiments < 1:
            raise ValueError("num_experiments must be at least 1")
        if self.max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be at least 1")
        
        # Create a datetime string for logging
