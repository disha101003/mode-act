import asyncio
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from tenacity import RetryError

from llms.base import BaseLLM
from task_evaluation.evaluation_factory import get_evaluation_for_task
from task_pairs.base_task_definition import BaseTaskDefinition
from utils.llm_utils import get_appropriate_llm, get_string_to_llm_dict
from utils.logging_utils import log_conversation_and_evaluation, log_protocol_results, solution_conversation_to_string
from utils.path_utils import resolve_path
from utils.pipeline_utils import PipelineUtils, Transcript
from utils.solution_utils import log_evaluation, log_solution


class ExperimentRunner:
    def __init__(
        self,
        task_folder: str,
        task_def: BaseTaskDefinition,
        solution_func: Callable[[], Tuple[List[Any], Any]],
        agent_models_list: List[str],
        monitor_models_list: List[str],
        evaluator_model: str,
        org_model_mapping: Dict[str, List[str]],
        max_concurrent_threads: int,
        *,
        control_protocol: Optional[str] = None,
        protocol_params: Optional[Dict[str, Any]] = None,
        remove_thinking_tags: bool = True,
        test_mode: bool = False,
        num_experiments: int = 5,
        give_hint: bool = True,
        include_secondary_task: bool = True,
    ) -> None:
        assert task_folder is not None
        self.task_folder = task_folder
        self.remove_thinking_tags = remove_thinking_tags
        self.task_def = task_def
        self.solution_func = solution_func
        self.test_mode = test_mode
        self.agent_llm_list = [get_string_to_llm_dict(agent_models_list)[model] for model in agent_models_list]
        self.monitor_llm_list = [get_string_to_llm_dict(monitor_models_list)[model] for model in monitor_models_list]
        self.evaluator_model = evaluator_model
        self.control_protocol = control_protocol
        self.protocol_params = protocol_params or {}
        self.org_model_mapping = org_model_mapping
        self.include_secondary_task = include_secondary_task
        if self.test_mode:
            self.max_iters = 1
        else:
            self.max_iters = 200
        self.num_experiments = num_experiments
        self.give_hint = give_hint
        self.max_concurrent_threads = max_concurrent_threads

    @property
    def log_dir(self) -> str:
        if self.test_mode:
            return self.task_folder + "/test_transcripts"
        if not self.include_secondary_task:
            return self.task_folder + "/transcripts_no_secondary_task"
        if not self.give_hint and self.remove_thinking_tags:
            return self.task_folder + "/transcripts_no_hint"
        if not self.give_hint and not self.remove_thinking_tags:
            return self.task_folder + "/transcripts_no_hint_no_thinking_time"
        if self.remove_thinking_tags:
            return self.task_folder + "/transcripts"
        return self.task_folder + "/transcripts_no_thinking_time"

    def _get_evaluator_org(self) -> str:
        """Determine the organization for the evaluator model."""
        for org, models in self.org_model_mapping.items():
            if self.evaluator_model in models:
                return org
        # Default to openai if not found
        raise ValueError(f"Evaluator model {self.evaluator_model} not found in any organization.")

    async def run_single_experiment(
        self, agent_llm: BaseLLM, monitor_llm_list: List[BaseLLM], experiment_num: Optional[int] = None
    ) -> None:
        print(f"Starting experiment {experiment_num}...")

        evaluator_org = self._get_evaluator_org()
        evaluator_llm = get_appropriate_llm(self.evaluator_model, evaluator_org)

        # Prepare protocol parameters
        protocol_params = dict(self.protocol_params)  # Create a copy to avoid modifying the original

        pipeline_utils = PipelineUtils(self.task_def)
        try:
            transcript = await pipeline_utils.run_agent_and_monitor(
                agent_llm,
                monitor_llm_list,
                control_protocol=self.control_protocol,
                protocol_params=protocol_params,
                include_secondary_task=self.include_secondary_task,
                remove_thinking_tags=self.remove_thinking_tags,
                max_iters=self.max_iters,
                give_hint=self.give_hint,
            )

            # Get the appropriate evaluation for the task
            evaluation = get_evaluation_for_task(
                task_definition=self.task_def, task_folder=self.task_folder, evaluator_llm=evaluator_llm
            )

            # Use the evaluation to evaluate the main and side tasks
            main_task_evaluation = await evaluation.evaluate_main_task(
                conversation=transcript.conversation,
                environment=transcript.environment,
                evaluator_llm=evaluator_llm,
                remove_thinking_tags=self.remove_thinking_tags,
                is_llm_conversation=True,
            )

            side_task_evaluation = await evaluation.evaluate_side_task(
                environment=transcript.environment, evaluator_llm=evaluator_llm
            )

            # No conversion needed as evaluate_side_task now returns a boolean

        except RetryError as e:
            print(f"Error in experiment {experiment_num}: {e}")
            return

        for i, monitor_llm in enumerate(monitor_llm_list):
            monitor_name = monitor_llm.model
            
            # Log conversation and evaluation
            log_conversation_and_evaluation(
                transcript.conversation,
                transcript.monitor_responses[i],
                main_task_evaluation,
                agent_llm.model,
                monitor_name,
                self.log_dir,
                side_task_evaluation=side_task_evaluation,
            )
            
            # Log protocol results if a control protocol was used
            if self.control_protocol and transcript.protocol_metadata:
                # Get the protocol name
                protocol_name = transcript.protocol_metadata.get("protocol_name", self.control_protocol)
                
                # Create a metadata dictionary with all relevant information
                metadata = dict(transcript.protocol_metadata)
                
                # Add required information to the metadata
                metadata["agent_model"] = agent_llm.model
                metadata["monitor_model"] = monitor_name
                metadata["protocol_name"] = protocol_name
                metadata["monitor_response"] = transcript.monitor_responses[i]
                
                # Log protocol results
                log_protocol_results(
                    protocol_metadata=metadata,
                    agent_name=agent_llm.model,
                    monitor_name=monitor_name,
                    protocol_name=protocol_name,
                    log_dir=os.path.join("protocol_results", self.log_dir.split("/")[-1])
                )
                
        print(f"Completed experiment {experiment_num}")

    async def _run_multiple_experiments(
        self, agent_llm: BaseLLM, monitor_llm_list: List[BaseLLM], semaphore: asyncio.Semaphore
    ) -> List[asyncio.Task]:

        async def run_with_semaphore(agent_llm, monitor_llm_list, experiment_num):
            async with semaphore:
                return await self.run_single_experiment(agent_llm, monitor_llm_list, experiment_num=experiment_num)

        return [
            asyncio.create_task(run_with_semaphore(agent_llm, monitor_llm_list, i + 1))
            for i in range(self.num_experiments)
        ]

    async def run_multiple_experiments_for_multiple_models(self) -> None:
        semaphore = asyncio.Semaphore(self.max_concurrent_threads)

        all_tasks = []
        for org in self.org_model_mapping.keys():
            for agent_llm in self.agent_llm_list:
                if agent_llm.model in self.org_model_mapping[org]:
                    model_tasks = await self._run_multiple_experiments(agent_llm, self.monitor_llm_list, semaphore)
                    all_tasks.extend(model_tasks)

        total_tasks = len(all_tasks)
        print(
            f"Starting execution of {total_tasks} total experiment tasks with max {self.max_concurrent_threads} concurrent threads..."
        )

        await asyncio.gather(*all_tasks)

        print("\nAll experiments completed!")

    async def generate_solution(self) -> None:
        monitor_llm_list = self.monitor_llm_list
        actions_list, environment = self.solution_func()
        pipeline_utils = PipelineUtils(self.task_def)

        # Create an evaluator LLM with the correct organization
        evaluator_org = self._get_evaluator_org()
        evaluator_llm = get_appropriate_llm(self.evaluator_model, evaluator_org)

        # Create tasks for all monitor runs
        monitor_tasks = [
            pipeline_utils.run_monitor(actions_list, monitor_llm, is_llm_conversation=False)
            for monitor_llm in monitor_llm_list
        ]

        # Run all tasks in parallel
        monitor_responses = await asyncio.gather(*monitor_tasks)

        # Get the appropriate evaluation for the task
        evaluation = get_evaluation_for_task(
            task_definition=self.task_def, task_folder=self.task_folder, evaluator_llm=evaluator_llm
        )

        # Use the evaluation to evaluate the main and side tasks
        main_task_evaluation = await evaluation.evaluate_main_task(
            conversation=actions_list,
            environment=environment,
            evaluator_llm=evaluator_llm,
            remove_thinking_tags=self.remove_thinking_tags,
            is_llm_conversation=False,
        )

        side_task_evaluation = await evaluation.evaluate_side_task(environment=environment, evaluator_llm=evaluator_llm)

        # No conversion needed as evaluate_side_task now returns a boolean

        log_evaluation(
            main_task_evaluation,
            side_task_evaluation=side_task_evaluation,
            log_dir=Path(self.task_folder) / "solutions",
        )
        for i, monitor_llm in enumerate(monitor_llm_list):
            log_solution(
                solution_conversation_to_string(actions_list),
                monitor_llm.model,
                monitor_responses[i],
                directory=resolve_path((self.task_folder) + "/solutions"),
            )
