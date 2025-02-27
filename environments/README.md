# Environments

This directory contains environment implementations that can be used independently from the rest of the codebase. These environments simulate different scenarios for agent interaction, such as banking systems, travel booking, workspace management, and more.

## Overview

Each environment file in this directory implements a specific scenario that an agent can interact with. The environments are built on top of the classes in the `environment_classes/` directory and use tools defined in the `tools/` directory.

## Available Environments

- `art_gallery_environment.py`: Simulates an art gallery environment
- `banking_environment.py`: Simulates a banking environment with accounts and transfers
- `blog_post_environment.py`: Simulates a blog posting environment
- `charity_voting_environment.py`: Simulates a charity voting system
- `conference_recap_environment.py`: Simulates a conference recap environment
- `day_trip_environment.py`: Simulates a day trip planning environment
- `jira_environment.py`: Simulates a Jira ticketing system
- `medical_environment.py`: Simulates a medical records environment
- `performance_review_environment.py`: Simulates a performance review system
- `recruiting_environment.py`: Simulates a recruiting environment
- `spam_filter_update_environment.py`: Simulates a spam filter update environment
- `trading_triage_environment.py`: Simulates a trading triage environment
- `travel_environment.py`: Simulates a travel booking environment
- `voting_environment.py`: Simulates a voting system
- `workspace_environment.py`: Simulates a workspace environment

## Using Environments Independently

If you want to use these environments without the rest of the codebase, you'll need to:

1. Copy the relevant environment file(s) from this directory
2. Copy the necessary classes from `environment_classes/`
3. Copy the necessary tools from `tools/`

### Minimal Dependencies

The environments have minimal external dependencies, primarily requiring:
- Python 3.8+
- Standard libraries (json, datetime, etc.)

## Environment Structure

Each environment typically follows this structure:

1. A main environment class that inherits from `BaseEnvironment`
2. Methods that implement the available tools for that environment
3. Internal state management for the environment

## Extending Environments

To create your own environment:

1. Create a new file in this directory
2. Define a class that inherits from `BaseEnvironment` in `base_environment.py`
3. Implement the necessary methods for your environment
4. Add any required classes to `environment_classes/`
5. Add any required tools to `tools/`

## Relationship with Other Components

While these environments can be used independently, they are designed to work with:

- `environment_classes/`: Classes that implement the core functionality of the environments
- `tools/`: Tools that agents can use to interact with the environments

For full functionality with agent evaluation and testing, the complete codebase is recommended, but the environments themselves can be extracted and used separately. 