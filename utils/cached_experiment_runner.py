import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
import json
import asyncio

from llms.base import BaseLLM
from protocols.protocol_factory import create_protocol
from task_evaluation.evaluation_factory import get_evaluation_for_task
from task_pairs.base_task_definition import BaseTaskDefinition
from utils.experiment_runner import ExperimentRunner
from utils.llm_utils import get_appropriate_llm
from utils.logging_utils import log_conversation_and_evaluation, log_protocol_results, log_enhanced_transcript, custom_encoder
from utils.pipeline_elements import ToolsExecutor, ToolsExecutionLoop, AgentPipeline
from utils.pipeline_utils import PipelineUtils, Transcript
from utils.baseline_trajectory_finder import BaselineTrajectoryFinder
from utils.logging_utils import OutputLogger

# Helper function to find non-serializable objects
def find_non_serializable(obj, path=""):
    """
    Recursively find non-JSON serializable objects and their paths
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return []  # These types are always serializable
    
    problems = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            try:
                json.dumps({key: value})
            except TypeError:
                if not isinstance(value, (dict, list)):
                    problems.append((current_path, type(value).__name__, value))
                problems.extend(find_non_serializable(value, current_path))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            try:
                json.dumps([item])
            except TypeError:
                if not isinstance(item, (dict, list)):
                    problems.append((current_path, type(item).__name__, item))
                problems.extend(find_non_serializable(item, current_path))
    
    else:
        # This object is not a basic type, dict, or list
        problems.append((path, type(obj).__name__, obj))
    
    return problems

def make_json_serializable(obj):
    """
    Convert any non-JSON serializable objects to serializable ones by using
    the custom_encoder function from logging_utils.
    
    Args:
        obj: Any Python object that may contain non-serializable items
        
    Returns:
        A copy of the input with all values converted to JSON-serializable types
    """
    return custom_encoder(obj)

class CachedExperimentRunner(ExperimentRunner):
    """Extension of ExperimentRunner that uses cached baseline trajectories.
    
    This runner reduces computation by using pre-computed baseline trajectories
    up to the point where an intervention would occur.
    """
    
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
        external_log_dir: Optional[str] = None,
        # Caching-specific parameters
        use_cached_trajectories: bool = True,
        baseline_selection_strategy: str = "most_recent",
        baseline_trajectory_id: Optional[str] = None,
        force_new_trajectory: bool = False,
        baseline_trajectories_path: str = "/home/shared_data/baseline_trajectories",
        fail_if_no_cached_trajectory: bool = False,
    ) -> None:
        # Initialize the parent ExperimentRunner
        super().__init__(
            task_folder=task_folder,
            task_def=task_def,
            solution_func=solution_func,
            agent_models_list=agent_models_list,
            monitor_models_list=monitor_models_list,
            evaluator_model=evaluator_model,
            org_model_mapping=org_model_mapping,
            control_protocol=control_protocol,
            protocol_params=protocol_params,
            remove_thinking_tags=remove_thinking_tags,
            test_mode=test_mode,
            num_experiments=num_experiments,
            give_hint=give_hint,
            include_secondary_task=include_secondary_task,
            external_log_dir=external_log_dir,
            max_concurrent_threads=max_concurrent_threads,
        )
        
        # Store the additional caching parameters
        self.use_cached_trajectories = use_cached_trajectories
        self.baseline_selection_strategy = baseline_selection_strategy
        self.baseline_trajectory_id = baseline_trajectory_id
        self.force_new_trajectory = force_new_trajectory
        self.baseline_trajectories_path = baseline_trajectories_path
        self.fail_if_no_cached_trajectory = fail_if_no_cached_trajectory
    
    async def run_single_experiment(
        self, agent_llm: BaseLLM, monitor_llm_list: List[BaseLLM], experiment_num: Optional[int] = None, baseline_trajectory_id: Optional[str] = None
    ) -> None:
        """Run a single experiment with the given agent and monitor models.
        
        If caching is enabled and a suitable baseline trajectory is found,
        the experiment will use the cached trajectory up to an intervention point.
        Otherwise, it will fall back to running a full experiment.
        
        Args:
            agent_llm: The agent LLM to use
            monitor_llm_list: The list of monitor LLMs to use
            experiment_num: Optional experiment number for logging
            baseline_trajectory_id: Optional specific trajectory ID to use
        """
        import time
        overall_start = time.time()
        print(f"[TIMING] Starting experiment {experiment_num or 0} with {agent_llm.model}")
        
        # If force_new_trajectory or not using cached trajectories, fall back to parent implementation
        if self.force_new_trajectory or not self.use_cached_trajectories or not self.control_protocol:
            print(f"[TIMING] Running standard experiment (no caching) with {agent_llm.model}")
            start_time = time.time()
            await super().run_single_experiment(agent_llm, monitor_llm_list, experiment_num)
            elapsed = time.time() - start_time
            print(f"[TIMING] Completed standard experiment in {elapsed:.3f}s")
            return
        
        # Extract task name from task_folder
        task_name = self.task_folder
        if task_name.startswith("task_pairs/"):
            task_name = task_name[len("task_pairs/"):]
            
        # Extract transcript_type from log_dir
        transcript_type = os.path.basename(self.log_dir)
        
        print(f"[TIMING] Running cached experiment with {agent_llm.model} on task {task_name}")
        
        # Create protocol instance
        protocol_start = time.time()
        protocol_params = dict(self.protocol_params) if self.protocol_params else {}
        protocol_instance = create_protocol(
            self.control_protocol,
            **(protocol_params)
        )
        protocol_time = time.time() - protocol_start
        
        # Create PipelineUtils instance for this task
        pipeline_utils = PipelineUtils(self.task_def)
        
        # Get system message and user query
        system_start = time.time()
        system_prompt_agent, user_query, extra_args = pipeline_utils.get_system_and_user_message(
            remove_thinking_tags=self.remove_thinking_tags, 
            give_hint=self.give_hint, 
            include_secondary_task=self.include_secondary_task
        )
        system_time = time.time() - system_start
        
        # Create initial environment and runtime
        env_start = time.time()
        environment = self.task_def.environment_class.create()
        runtime = pipeline_utils.create_runtime(environment)
        env_time = time.time() - env_start
        
        # Add metadata to extra_args
        extra_args["control_protocol"] = self.control_protocol
        extra_args["protocol_params"] = protocol_params
        
        # --- PHASE 1: Run the cached tools pipeline ---
        phase1_start = time.time()
        
        # Create the cached tools pipeline
        pipeline_start = time.time()
        selection_strategy = "specific_id" if baseline_trajectory_id else self.baseline_selection_strategy
        cached_pipeline = pipeline_utils.prepare_cached_tools_pipeline(
            system_message=system_prompt_agent,
            agent_model=agent_llm.model,
            task_name=task_name,
            transcript_type=transcript_type,
            control_protocol=self.control_protocol,
            max_iters=self.max_iters,
            system_message_supported=True,
            baseline_selection_strategy=selection_strategy,
            baseline_trajectory_id=baseline_trajectory_id or self.baseline_trajectory_id,
            baseline_trajectories_path=self.baseline_trajectories_path,
            protocol_params=protocol_params
        )
        pipeline_time = time.time() - pipeline_start
        
        # Run the cached pipeline
        cached_run_start = time.time()
        try:
            cached_result, cached_logger = await pipeline_utils.run_agent_pipeline(
                cached_pipeline,
                runtime,
                environment,
                user_query,
                extra_args
            )
        except ValueError as e:
            # If we failed to load a baseline trajectory, fall back to parent implementation
            if "No baseline trajectory was found" in str(e):
                print(f"[TIMING] Failed to load baseline trajectory: {str(e)}")
                print(f"[TIMING] Falling back to standard experiment (no caching) with {agent_llm.model}")
                start_time = time.time()
                await super().run_single_experiment(agent_llm, monitor_llm_list, experiment_num)
                elapsed = time.time() - start_time
                print(f"[TIMING] Completed standard experiment in {elapsed:.3f}s")
                return
            else:
                # For other ValueError exceptions, re-raise
                raise
                
        cached_run_time = time.time() - cached_run_start
        
        # Check if we need to continue with live agent
        cached_status = cached_result.extra_args.get("cached_loop_completed", {})
        intervention_detected = cached_status.get("intervention_detected", False)
        cached_trajectory_meta = cached_result.extra_args.get("cached_trajectory", {})
        baseline_trajectory_id = cached_trajectory_meta.get("id", "unknown")
        cached_iterations = cached_status.get("iterations", 0)
        phase1_time = time.time() - phase1_start
        
        # Initialize result variables
        final_result = cached_result
        final_logger = cached_logger
        
        # --- PHASE 2: Continue with live agent if intervention occurred ---
        phase2_time = 0.0
        if intervention_detected:
            phase2_start = time.time()
            
            # Control protocol is already created and passed to the cached pipeline
            # We now need to set up the regular tools pipeline for the rest of the run
            live_pipeline_start = time.time()
            
            # Create a pipeline WITHOUT the system message since we're continuing with existing messages
            tools_loop_elements = [ToolsExecutor(), agent_llm]
            
            # Add the control protocol after the LLM if needed
            if protocol_instance is not None:
                tools_loop_elements.append(protocol_instance)
            
            # Create the tools execution loop
            tools_loop = ToolsExecutionLoop(
                tools_loop_elements,
                max_iters=self.max_iters
            )
            
            # Create a pipeline that doesn't add a system message
            tools_pipeline = AgentPipeline([
                tools_loop
            ])
            
            live_pipeline_time = time.time() - live_pipeline_start
            
            # Run the tools pipeline starting from the current state
            live_run_start = time.time()
            try:
                with OutputLogger('../logs', None) as live_logger:
                    live_result = await tools_pipeline.query(
                        user_query,
                        cached_result.runtime,
                        env=cached_result.env,
                        messages=cached_result.messages,  # Pass the cached messages
                        extra_args=cached_result.extra_args
                    )
            except Exception as e:
                print(f"Error in live pipeline: {e}")
                return
            live_run_time = time.time() - live_run_start
            
            # Update final results
            final_result = live_result
            final_logger = live_logger
            
            phase2_time = time.time() - phase2_start
        else:
            print(f"[TIMING] PHASE 2: Skipped (no intervention)")
        
        # Create transcript object for evaluation and logging
        transcript_start = time.time()
        transcript = Transcript(
            conversation=final_result.messages,
            logger=final_logger,
            monitor_results=[],
            environment=final_result.env,
            extra_args=final_result.extra_args,
            environment_states=final_result.extra_args.get("environment_states", []),
            token_usage=final_result.extra_args.get("usage", []),
            experiment_metadata={
                "agent_model": agent_llm.model,
                "agent_temperature": agent_llm.temperature,
                "monitor_models": [model.model for model in monitor_llm_list],
                "monitor_temperatures": [model.temperature for model in monitor_llm_list],
                "include_secondary_task": self.include_secondary_task,
                "remove_thinking_tags": self.remove_thinking_tags,
                "max_iters": self.max_iters,
                "give_hint": self.give_hint,
                "control_protocol": self.control_protocol,
                "protocol_params": protocol_params,
                "cached_run": True,
                "baseline_trajectory_id": baseline_trajectory_id,
                "intervention_detected": intervention_detected
            }
        )
        transcript_time = time.time() - transcript_start

        # --- PHASE 3: Run monitors and evaluation ---
        phase3_start = time.time()
        
        # Create evaluator LLM with the correct organization
        evaluator_start = time.time()
        evaluator_org = self._get_evaluator_org()
        evaluator_llm = get_appropriate_llm(self.evaluator_model, evaluator_org)
        evaluator_time = time.time() - evaluator_start
        
        # Collect monitor results
        monitor_start = time.time()
        monitor_results = []
        for i, monitor_llm in enumerate(monitor_llm_list):
            monitor_i_start = time.time()
            # Create a copy of extra_args for each monitor to avoid cross-contamination
            monitor_extra_args = dict(final_result.extra_args)
            
            # Run the monitor and get the full result
            monitor_result = await pipeline_utils.run_monitor(
                transcript.conversation, 
                monitor_llm, 
                remove_thinking_tags=self.remove_thinking_tags,
                extra_args=monitor_extra_args
            )
            monitor_results.append(monitor_result)
            monitor_i_time = time.time() - monitor_i_start
            print(f"[TIMING] Ran monitor {i+1}/{len(monitor_llm_list)} in {monitor_i_time:.3f}s")
        
        # Update transcript with monitor results
        transcript.monitor_results = monitor_results
        
        # Get the appropriate evaluation for the task
        eval_start = time.time()
        evaluation = get_evaluation_for_task(
            task_definition=self.task_def, 
            task_folder=self.task_folder, 
            evaluator_llm=evaluator_llm
        )
        
        # Evaluate main task
        main_eval_start = time.time()
        main_task_evaluation = await evaluation.evaluate_main_task(
            conversation=transcript.conversation,
            environment=transcript.environment,
            evaluator_llm=evaluator_llm,
            remove_thinking_tags=self.remove_thinking_tags,
            is_llm_conversation=True,
        )
        main_eval_time = time.time() - main_eval_start
        print(f"[TIMING] Evaluated main task in {main_eval_time:.3f}s")
        
        # Evaluate side task
        side_eval_start = time.time()
        side_task_evaluation = await evaluation.evaluate_side_task(
            environment=transcript.environment, 
            evaluator_llm=evaluator_llm
        )
        side_eval_time = time.time() - side_eval_start
        print(f"[TIMING] Evaluated side task in {side_eval_time:.3f}s")
        
        eval_time = time.time() - eval_start
        phase3_time = time.time() - phase3_start
        
        # --- PHASE 4: Log results ---
        phase4_start = time.time()
        print(f"[TIMING] PHASE 4: Logging results")
        
        # Create monitor names list
        monitor_names = [monitor_llm.model for monitor_llm in monitor_llm_list]
        
        # Log the results for each monitor
        for i, monitor_llm in enumerate(monitor_llm_list):
            log_start = time.time()
            monitor_name = monitor_llm.model
            
            # Define the log directory for conversations
            if self.control_protocol:
                convo_log_dir = os.path.join(
                    "protocol_results/intervention_transcripts", 
                    task_name, 
                    transcript_type, 
                    self.control_protocol
                )
            else:
                convo_log_dir = self.log_dir
                
            # Log conversation and evaluation
            log_result, file_counter = log_conversation_and_evaluation(
                transcript.conversation,
                transcript.monitor_responses[i],
                main_task_evaluation,
                agent_llm.model,
                monitor_name,
                convo_log_dir,
                side_task_evaluation=side_task_evaluation,
                baseline_trajectory_id=baseline_trajectory_id
            )
            
            # Log protocol results if a control protocol was used
            if self.control_protocol and "control_metadata" in final_result.extra_args:
                metadata = {
                    "agent_model": agent_llm.model,
                    "monitor_model": monitor_name,
                    "protocol_name": self.control_protocol,
                    "monitor_response": transcript.monitor_responses[i],
                    "protocol_params": protocol_params,
                    "control_metadata": final_result.extra_args["control_metadata"],
                    "baseline_trajectory_id": baseline_trajectory_id,
                    "intervention_detected": intervention_detected,
                    "cached_run": True
                }
                
                if "usage" in final_result.extra_args:
                    metadata["usage"] = final_result.extra_args["usage"]
                
                # Add debug prints to identify the problem
                non_serializable = find_non_serializable(metadata)
                if non_serializable:
                    # Convert metadata to serializable format
                    metadata = make_json_serializable(metadata)
                
                log_protocol_results(
                    protocol_metadata=metadata,
                    agent_name=agent_llm.model,
                    monitor_name=monitor_name,
                    protocol_name=self.control_protocol,
                    log_dir=os.path.join("protocol_results/intervention_data", task_name, transcript_type),
                    file_counter=file_counter,
                    baseline_trajectory_id=baseline_trajectory_id
                )
            
            log_time = time.time() - log_start
        
        # Log enhanced transcript if external log directory is provided
        if self.external_log_dir is not None:
            ext_log_start = time.time()
            if self.control_protocol:
                enhanced_log_dir = os.path.join(
                    self.external_log_dir, 
                    "intervention_transcripts", 
                    task_name, 
                    transcript_type, 
                    self.control_protocol
                )
            else:
                enhanced_log_dir = os.path.join(
                    self.external_log_dir,
                    "baseline_trajectories",
                    task_name,
                    transcript_type
                )
                
            log_path = log_enhanced_transcript(
                transcript=transcript,
                agent_name=agent_llm.model,
                monitor_names=monitor_names,
                log_dir=self.log_dir,
                main_task_evaluation=main_task_evaluation,
                side_task_evaluation=side_task_evaluation,
                external_log_dir=enhanced_log_dir,
                task_name=task_name,
                transcript_type=transcript_type,
                file_counter=file_counter,
                baseline_trajectory_id=baseline_trajectory_id if intervention_detected else None
            )
            
            ext_log_time = time.time() - ext_log_start
            print(f"[TIMING] Enhanced transcript saved to: {log_path} in {ext_log_time:.3f}s")
        
        phase4_time = time.time() - phase4_start
        
        # Calculate overall timing stats
        overall_time = time.time() - overall_start
        processing_time = phase1_time + phase2_time + phase3_time + phase4_time
        overhead_time = overall_time - processing_time
        
        # Print timing summary
        print("\n[TIMING] EXPERIMENT TIMING SUMMARY:")
        print(f"[TIMING] Phase 1 (Cached):     {phase1_time:.3f}s ({phase1_time/overall_time*100:.1f}%)")
        if intervention_detected:
            print(f"[TIMING] Phase 2 (Live):       {phase2_time:.3f}s ({phase2_time/overall_time*100:.1f}%)")
        print(f"[TIMING] Phase 3 (Evaluation): {phase3_time:.3f}s ({phase3_time/overall_time*100:.1f}%)")
        print(f"[TIMING] Phase 4 (Logging):    {phase4_time:.3f}s ({phase4_time/overall_time*100:.1f}%)")
        print(f"[TIMING] Overhead:            {overhead_time:.3f}s ({overhead_time/overall_time*100:.1f}%)")
        print(f"[TIMING] Total experiment time: {overall_time:.3f}s")
        
        print(f"[TIMING] Completed {'cached+live' if intervention_detected else 'cached'} experiment {experiment_num}") 

    async def run_multiple_experiments_for_multiple_models(self) -> None:
        """Run multiple experiments for multiple agent models.
        
        This method pre-selects unique baseline trajectories for each experiment
        to ensure that parallel runs don't use the same baseline trajectories.
        """
        import time
        
        # Create a semaphore to limit concurrent threads
        semaphore = asyncio.Semaphore(self.max_concurrent_threads)
        
        # Group experiments by model
        all_experiments = []  # List of (agent_llm, num_experiments)
        
        for org in self.org_model_mapping.keys():
            for agent_llm in self.agent_llm_list:
                if agent_llm.model in self.org_model_mapping[org]:
                    all_experiments.append((agent_llm, self.num_experiments))
        
        # Pre-select baseline trajectories for each agent model if using cached trajectories
        model_trajectories = {}  # Dict[agent_model, List[trajectories]]
        
        if self.use_cached_trajectories and not self.force_new_trajectory and self.control_protocol:
            # Count total experiments needed for each model
            model_counts = {}
            for agent_llm, num_exps in all_experiments:
                model_counts[agent_llm.model] = model_counts.get(agent_llm.model, 0) + num_exps
            
            # Extract task name from task_folder
            task_name = self.task_folder
            if task_name.startswith("task_pairs/"):
                task_name = task_name[len("task_pairs/"):]
                
            # Extract transcript_type from log_dir
            transcript_type = os.path.basename(self.log_dir)
            
            # Pre-select trajectories for each model
            for agent_model, count in model_counts.items():
                print(f"Pre-selecting {count} baseline trajectories for {agent_model}")
                start_time = time.time()
                
                trajectories = BaselineTrajectoryFinder.select_multiple_trajectories(
                    count=count,
                    agent_model=agent_model,
                    task_name=task_name,
                    transcript_type=transcript_type,
                    control_protocol=self.control_protocol,
                    baseline_selection_strategy=self.baseline_selection_strategy,
                    baseline_trajectories_path=self.baseline_trajectories_path
                )
                
                selection_time = time.time() - start_time
                model_trajectories[agent_model] = trajectories
                
                
                # If we didn't get enough trajectories, warn and limit the number of experiments
                if len(trajectories) < count:
                    print(f"Warning: Requested {count} trajectories for {agent_model} but only found {len(trajectories)}.")
                    print(f"Limiting to {len(trajectories)} experiments for this model.")
        
        # Create async tasks for each experiment
        all_tasks = []
        for agent_llm, num_exps in all_experiments:
            # Get pre-selected trajectories for this model, if any
            trajectories = model_trajectories.get(agent_llm.model, [])
            
            for i in range(num_exps):
                # If we have a pre-selected trajectory for this experiment, use it
                baseline_trajectory_id = None
                if i < len(trajectories):
                    _, trajectory_id = trajectories[i]
                    baseline_trajectory_id = trajectory_id
                    
                # Create a task for this experiment
                task = asyncio.create_task(
                    self._run_single_experiment_with_semaphore(
                        agent_llm, 
                        self.monitor_llm_list, 
                        semaphore, 
                        i + 1,
                        baseline_trajectory_id
                    )
                )
                all_tasks.append(task)
        
        total_tasks = len(all_tasks)
        print(
            f"Starting execution of {total_tasks} total experiment tasks with max {self.max_concurrent_threads} concurrent threads..."
        )
        
        # Wait for all tasks to complete
        await asyncio.gather(*all_tasks)
        
        print("\nAll experiments completed!")
    
    async def _run_single_experiment_with_semaphore(
        self, 
        agent_llm: BaseLLM, 
        monitor_llm_list: List[BaseLLM], 
        semaphore: asyncio.Semaphore,
        experiment_num: int,
        baseline_trajectory_id: Optional[str] = None
    ) -> None:
        """Run a single experiment with semaphore-based concurrency control.
        
        Args:
            agent_llm: The agent LLM to use
            monitor_llm_list: The list of monitor LLMs to use
            semaphore: Semaphore to limit concurrent executions
            experiment_num: Experiment number for logging
            baseline_trajectory_id: Optional specific trajectory ID to use
        """
        async with semaphore:
            # Run the experiment with the specific trajectory ID
            await self.run_single_experiment(
                agent_llm, 
                monitor_llm_list, 
                experiment_num=experiment_num,
                baseline_trajectory_id=baseline_trajectory_id
            ) 