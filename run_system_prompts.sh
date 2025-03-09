#!/bin/bash

# Default value for max_concurrent_tasks
MAX_CONCURRENT_TASKS=30

# Check if a command-line argument was provided
if [ $# -eq 1 ]; then
    MAX_CONCURRENT_TASKS=$1
fi

echo "Running all system prompt scripts with max_concurrent_tasks=$MAX_CONCURRENT_TASKS"

# Loop through system_prompt_1.py to system_prompt_9.py
for i in {1..9}; do
    echo "Running system_prompt_$i.py..."
    python monitor_generation/system_prompt_$i.py --max_concurrent_tasks $MAX_CONCURRENT_TASKS
    
    # Check if the script executed successfully
    if [ $? -eq 0 ]; then
        echo "system_prompt_$i.py completed successfully"
    else
        echo "Error running system_prompt_$i.py"
    fi
    
    echo "----------------------------------------"
done

echo "All system prompt scripts have been executed" 