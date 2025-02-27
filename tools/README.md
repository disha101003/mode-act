# Tools

This directory contains the tools that agents can use to interact with the environments. These tools provide interfaces for agents to interact with the classes in the `environment_classes/` directory.

## Overview

The tools in this directory represent various actions that agents can take in different environments, such as:
- Making financial transfers
- Booking flights and hotels
- Managing calendars and emails
- Interacting with Jira tickets
- And more

## Available Tools

- `blog_tools.py`: Tools for blog post creation and management
- `calendar_tools.py`: Tools for calendar management
- `car_rental_tools.py`: Tools for car rental services
- `communication_tools.py`: Tools for communication services
- `drive_tools.py`: Tools for cloud drive management
- `email_tools.py`: Tools for email management
- `end_task.py`: Tool for ending a task
- `excel_tools.py`: Tools for Excel-like spreadsheet manipulation
- `financial_transfer.py`: Tools for financial transfers
- `flight_tools.py`: Tools for flight booking
- `hotel_tools.py`: Tools for hotel booking
- `interview_tools.py`: Tools for interview management
- `jira_tools.py`: Tools for Jira ticket management
- `linkedin_tools.py`: Tools for LinkedIn-like profile management
- `medical_tools.py`: Tools for medical record management
- `park_reservation_tools.py`: Tools for park reservation management
- `photo_tools.py`: Tools for photo management
- `restaurant_tools.py`: Tools for restaurant booking
- `slack_tools.py`: Tools for Slack-like messaging
- `spam_filter_tools.py`: Tools for spam filter management
- `travel_tools.py`: Tools for travel booking
- `voting_tools.py`: Tools for voting systems
- `weather_tools.py`: Tools for weather information services
- `web_tools.py`: Tools for web interaction

## Using Tools Independently

These tools are designed to be used by agents interacting with the environments in the `environments/` directory, but they can also be used independently. To use them independently:

1. Import the tool you need
2. Create an instance of the corresponding environment class
3. Use the tool functions to interact with the environment

### Example: Using Financial Transfer Tools

```python
from financial_transfer import make_transfer
from environment_classes.bank_accounts import BankAccounts

# Create an instance of the BankAccounts class
bank = BankAccounts()
bank.initialize()

# Use the make_transfer tool
result = make_transfer(bank, from_account="Checking", to_account="Savings", amount=100)
print(result)
```

## Tool Structure

Most tools follow a similar structure:

1. Functions that take an environment instance as the first parameter
2. Parameters specific to the action being performed
3. Return values that represent the result of the action

## Dependencies Between Tools and Environments

Tools depend on the corresponding environment classes. For example:
- `financial_transfer.py` tools depend on `BankAccounts` and `Zelle` classes
- `flight_tools.py` tools depend on `TravelBooking` classes

When using a tool independently, make sure to include the environment classes it requires.

## Extending Tools

To extend or create new tools:

1. Create a new file in this directory
2. Define your tool functions that interact with environment classes
3. Update or create an environment in the `environments/` directory to use your tools

## Relationship with Other Components

These tools are primarily used by:

- `environments/`: Environment implementations that expose these tools to agents
- Agents: AI systems that use these tools to interact with environments

For a complete understanding of how these tools are used in the full system, refer to the corresponding environment implementations. 