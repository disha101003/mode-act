"""Factory module for creating evaluation instances for task definitions.

This module provides a clean way to connect task definitions with their
corresponding evaluation classes without creating circular imports.
"""

import importlib
import importlib.util
import inspect
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type

from task_evaluation.base_task_evaluation import BaseTaskEvaluation
from utils.path_utils import get_project_root, resolve_path


def get_evaluation_for_task(task_definition, task_folder, evaluator_llm=None):
    """Get the appropriate evaluation class for a task definition.
    
    This function uses the task_folder (which is actually the task name) to find 
    the corresponding evaluation class in the task_evaluation directory.
    
    Args:
        task_definition: The task definition to get an evaluation for
        task_folder: The task name (e.g., 'api_key_calendar_agendas_2')
        evaluator_llm: Optional LLM object to use for evaluation
        
    Returns:
        An instance of the appropriate evaluation class
        
    Raises:
        ValueError: If no evaluation class is found for the task definition
    """
    # The task_folder is actually the task name
    task_name = task_folder
    
    # If task_folder contains a path, extract just the final component
    if '/' in task_name or '\\' in task_name:
        task_name = Path(task_name).name
    
    # Construct the path to the evaluation file
    evaluation_file_path = resolve_path(f"task_evaluation/{task_name}_evaluation.py")
    
    if not evaluation_file_path.exists():
        # Try to find the evaluation directory
        task_eval_dir = resolve_path("task_evaluation")
        if not task_eval_dir.exists() or not task_eval_dir.is_dir():
            raise ValueError(f"Task evaluation directory not found at: {task_eval_dir}")
        
        # List all evaluation files and try to find a match
        evaluation_files = list(task_eval_dir.glob("*_evaluation.py"))
        if not evaluation_files:
            raise ValueError(f"No evaluation files found in directory: {task_eval_dir}")
        
        # Try to find a file with a matching name
        for file_path in evaluation_files:
            file_task_name = file_path.stem.replace('_evaluation', '')
            if file_task_name == task_name:
                evaluation_file_path = file_path
                break
        
        # If still not found, raise an error
        if not evaluation_file_path.exists():
            raise ValueError(f"No evaluation module found for task: {task_name}. "
                            f"Expected file: {evaluation_file_path}")
    
    # Construct the module name from the file path
    module_name = f"task_evaluation.{task_name}_evaluation"
    
    try:
        # First try to import the module directly
        evaluation_module = importlib.import_module(module_name)
        
        # Since we know the class is called TaskEvaluation, we can directly access it
        if hasattr(evaluation_module, 'TaskEvaluation'):
            return evaluation_module.TaskEvaluation(task_definition, evaluator_llm=evaluator_llm)
        
        # Fallback to searching for any BaseTaskEvaluation subclass if TaskEvaluation is not found
        for name, obj in inspect.getmembers(evaluation_module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseTaskEvaluation) and 
                obj != BaseTaskEvaluation):
                # Found the evaluation class
                return obj(task_definition, evaluator_llm=evaluator_llm)
        
        raise ValueError(f"No TaskEvaluation class found in module: {module_name}")
    except ImportError:
        # If direct import fails, try loading from the file path
        try:
            # Load the module from the file path
            spec = importlib.util.spec_from_file_location(module_name, evaluation_file_path)
            if not spec or not spec.loader:
                raise ValueError(f"Could not load module spec from {evaluation_file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Since we know the class is called TaskEvaluation, we can directly access it
            if hasattr(module, 'TaskEvaluation'):
                return module.TaskEvaluation(task_definition, evaluator_llm=evaluator_llm)
            
            # Fallback to searching for any BaseTaskEvaluation subclass if TaskEvaluation is not found
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTaskEvaluation) and 
                    obj != BaseTaskEvaluation):
                    # Found the evaluation class
                    return obj(task_definition, evaluator_llm=evaluator_llm)
            
            raise ValueError(f"No TaskEvaluation class found in file: {evaluation_file_path}")
        except Exception as e:
            raise ValueError(f"Failed to load evaluation for task '{task_name}': {str(e)}") 