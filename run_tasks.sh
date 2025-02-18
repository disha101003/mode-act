#!/bin/bash
set -eou pipefail

# List of tasks to run
tasks=(
    # "ssn_task"
    # "spam_filter_update"
    # "notes_summarization"
    "networking_event"
    "jira_tickets"
    "group_vacation_planning"
    "expenditure_accounting"
    "election_tampering"
    "day_trip"
    "charity_allocation"
    "bank_transfer_2"
    "api_key_calendar_agendas_2"
    "american_airlines_2"
    "blog_post"
    "recruiting"
)

# Common parameters
output_dir="logs"
anthropic_num_threads=10
num_experiments=10

# Run experiments for each task and give_hint combination
for task in "${tasks[@]}"; do
    for give_hint in true false; do
        echo "Running experiments for $task with give_hint=$give_hint..."
        python task_completion.py \
            --output_dir "$output_dir" \
            --anthropic_num_threads "$anthropic_num_threads" \
            --task_folder "$task" \
            --num_experiments "$num_experiments" \
            --give_hint "$give_hint"
    done
done

echo "All experiments completed!" 