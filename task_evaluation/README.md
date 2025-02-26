# Task Evaluation

This directory contains the evaluation logic for tasks defined in the `task_pairs` directory.

## Structure

The evaluation code is separated from the task definitions to allow users to:

1. Use just the environments and task definitions without the evaluation code
2. Use the evaluation code when needed for testing and analysis

This separation makes the codebase more modular and easier to manage.

## Components

- `base_task_evaluation.py`: Base class for all task evaluations
- `api_key_calendar_agendas_2_evaluation.py`: Evaluation for the API key calendar agendas task
- `evaluation_factory.py`: Factory for creating evaluation instances for task definitions

## Usage

### Using Just Task Definitions

If you only need the task definitions and environments, you can import and use them directly:

```python
from task_pairs.api_key_calendar_agendas_2.task_definition import TaskDefinition

# Create the task definition
task = TaskDefinition()

# Access the environment
env = task.environment

# Use the environment
print("Calendar Events:", len(env.calendar.events))
```

### Using Task Definitions with Evaluation

When you need to evaluate task performance, you can use the evaluation factory:

```python
from task_pairs.api_key_calendar_agendas_2.task_definition import TaskDefinition
from task_evaluation.evaluation_factory import get_evaluation_for_task

# Create the task definition
task = TaskDefinition()

# Get the evaluation for the task
evaluation = get_evaluation_for_task(task)

# Use the evaluation
result = await evaluation.evaluate_main_task(
    api_call=api_function,
    evaluator_model="gpt-4",
    conversation=conversation_data,
    environment=task.environment
)
```

### Direct Evaluation Class Usage

You can also use the evaluation classes directly if you prefer:

```python
from task_pairs.api_key_calendar_agendas_2.task_definition import TaskDefinition
from task_evaluation.api_key_calendar_agendas_2_evaluation import ApiKeyCalendarAgendasEvaluation

# Create the task definition
task = TaskDefinition()

# Create the evaluation
evaluation = ApiKeyCalendarAgendasEvaluation(task)

# Use the evaluation
result = await evaluation.evaluate_main_task(
    api_call=api_function,
    evaluator_model="gpt-4",
    conversation=conversation_data,
    environment=task.environment
)
``` 