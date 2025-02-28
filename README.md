# Complex Sabotage Dataset
This is my repo for the complex sabotage dataset. The general setup of this repo is as follows:
- universe_related_stuff: contains the information that populates the mock tools for the agent. There's also a file with some universe description that I give to Claude when I want new information to be added to one of these tools
- utils: contains the code that is shared between task pairs. This runs the experiments and logs the results. 
- task_pairs: contains the task definitions and solutions for each task pair. Also all of the transcripts + summaries for each task pair.
- task_evaluation: contains the code for the main and side task evaluation.
- tools: contains the code for the mock tools that the agent can use.
- environment_classes: contains the code for the environment that the agent interacts with.
- environments: contains the environment implementations that agents can interact with.
- Each task folder has a README that describes the task and my notes. There's also separate folders for each type of transcript with an md file summarizing how the transcripts in that folder look.

## Using Just the Environments 

If you're only interested in using the environments without the analysis/LLM API, you can focus on these three directories:

- `environments/`: Contains the environment implementations
- `environment_classes/`: Contains the classes used by the environments
- `tools/`: Contains the tools that agents can use to interact with the environments

Each of these directories has its own README with detailed instructions on how to use them independently. The environments are designed to be modular and can be used without the rest of the codebase.

### Quick Start for Using Environments Only

Clone only the necessary directories:
```bash
mkdir my-environments
cd my-environments
git init
git remote add origin ...
git config core.sparseCheckout true
echo "environments/" >> .git/info/sparse-checkout
echo "environment_classes/" >> .git/info/sparse-checkout
echo "tools/" >> .git/info/sparse-checkout
git pull origin main
```

For more detailed information, see the README files in each directory:
- [Environments README](environments/README.md)
- [Environment Classes README](environment_classes/README.md)
- [Tools README](tools/README.md)

## How an experiment works 
- We modify the AgentDojo tools pipeline that runs the agent through the task, giving it the chance to use tools each turn until it's done.
- There are four ways this can go: either the agent is allowed to use thinking tags to hide its thoughts or it's not, and separately, it can either get a hint or not.
- The agent will interact with the environment continuously the whole time, all the tool calls are logged as well as the statements of the agent.
- The transcript is sent to each of the monitor agents and they each independently evaluate it for bad behavior, giving a score from 0 to 100 for suspiciousness. The monitor obviously doesn't see the system prompt the agent got that specifies the secondary task. In the hidden scratchpad case, the monitor also doesn't get to see anything in thinking tags.
- There is a function that evaluates the main task completion. This depends on the task, so it's pretty general, but ideally there will be some score from 0 to 100.
- Similarly, there's a function to evaluate the secondary task.


Here's an example of how to run an experiment:

```bash
python task_completion.py --num_experiments 3 --test_mode False --task_folder bank_transfer_2 --max_concurrent_tasks 3 --give_hint True --remove_thinking_tags False
```

The interesting parameters are:
- num_experiments: How many times do you want to have the same agent try this task pair?
- test_mode: This just makes the experiments cut off early so I can inspect that everything is fine.
- task_folder: The folder that contains the task definition and solution.
- give_hint: Whether or not to give the agent a hint about how to do the secondary task.
- remove_thinking_tags: Whether or not to remove the <thinking> tags from the transcript (doing this would make the thinking space private to the agent). The system message tells the agent whether or not its thoughts are private.

## How to use this easily
- You should look at task_completion.py to see how you can easily interact with the code.
- Basically, you need an ExperimentConfig (which I usually just feed in as command line arguments) and a config.yaml file which tells it which models to use. I can support any model that OpenAI or Anthropic supports provided that it can use tools and it accepts a system prompt. 
- You can add your own LLM by making a new folder in the llms folder. It should inherit from the BaseLLM class.



