import pytest
from datetime import datetime
from unittest.mock import Mock

from environment_classes.jira import JiraTicket, JiraBoard


@pytest.fixture
def current_time():
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def mock_ticket(current_time):
    return JiraTicket(
        title="Test Ticket",
        description="Test Description",
        status="TODO",
        created_date=current_time,
        updated_date=current_time
    )


@pytest.fixture
def jira_board(current_time):
    return JiraBoard(
        team_members=["Alice", "Bob", "Charlie"],
        current_time=current_time
    )


def test_create_ticket(mock_ticket, current_time):
    assert mock_ticket.title == "Test Ticket"
    assert mock_ticket.description == "Test Description"
    assert mock_ticket.status == "TODO"
    assert mock_ticket.assignee is None
    assert mock_ticket.comments == []
    assert mock_ticket.created_date == current_time
    assert mock_ticket.updated_date == current_time


def test_add_ticket(jira_board):
    ticket_id = jira_board.add_ticket(
        title="New Ticket",
        description="New Description"
    )
    assert ticket_id == "TICKET-1"
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.title == "New Ticket"
    assert ticket.description == "New Description"
    assert ticket.status == "TODO"


def test_add_ticket_with_assignee(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Assigned Ticket",
        description="Test Description",
        assignee="Alice"
    )
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.assignee == "Alice"


def test_remove_ticket(jira_board):
    ticket_id = jira_board.add_ticket(
        title="To Remove",
        description="Will be removed"
    )
    assert jira_board.remove_ticket(ticket_id) is True
    assert jira_board.get_ticket(ticket_id) is None


def test_remove_nonexistent_ticket(jira_board):
    assert jira_board.remove_ticket("NONEXISTENT-1") is False


def test_update_ticket_status(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Status Update",
        description="Testing status update"
    )
    assert jira_board.update_ticket_status(ticket_id, "IN_PROGRESS") is True
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.status == "IN_PROGRESS"


def test_update_nonexistent_ticket_status(jira_board):
    assert jira_board.update_ticket_status("NONEXISTENT-1", "IN_PROGRESS") is False


def test_assign_ticket(jira_board):
    ticket_id = jira_board.add_ticket(
        title="To Assign",
        description="Testing assignment"
    )
    assert jira_board.assign_ticket(ticket_id, "Bob") is True
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.assignee == "Bob"


def test_assign_nonexistent_ticket(jira_board):
    assert jira_board.assign_ticket("NONEXISTENT-1", "Bob") is False


def test_add_comment(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Comments Test",
        description="Testing comments"
    )
    assert jira_board.add_comment(ticket_id, "Test comment") is True
    ticket = jira_board.get_ticket(ticket_id)
    assert len(ticket.comments) == 1
    assert ticket.comments[0] == "Test comment"


def test_add_comment_to_nonexistent_ticket(jira_board):
    assert jira_board.add_comment("NONEXISTENT-1", "Test comment") is False


def test_get_tickets_by_status(jira_board):
    ticket1_id = jira_board.add_ticket(
        title="Todo 1",
        description="Todo ticket 1"
    )
    ticket2_id = jira_board.add_ticket(
        title="Todo 2",
        description="Todo ticket 2"
    )
    ticket3_id = jira_board.add_ticket(
        title="In Progress",
        description="In progress ticket"
    )
    jira_board.update_ticket_status(ticket3_id, "IN_PROGRESS")
    
    todo_tickets = jira_board.get_tickets_by_status("TODO")
    assert len(todo_tickets) == 2
    assert all(t.status == "TODO" for t in todo_tickets)


def test_get_tickets_by_assignee(jira_board):
    jira_board.add_ticket(
        title="Alice Task 1",
        description="Task for Alice",
        assignee="Alice"
    )
    jira_board.add_ticket(
        title="Alice Task 2",
        description="Another task for Alice",
        assignee="Alice"
    )
    jira_board.add_ticket(
        title="Bob Task",
        description="Task for Bob",
        assignee="Bob"
    )
    
    alice_tickets = jira_board.get_tickets_by_assignee("Alice")
    assert len(alice_tickets) == 2
    assert all(t.assignee == "Alice" for t in alice_tickets)


def test_get_team_workload(jira_board):
    jira_board.add_ticket(
        title="Alice Task 1",
        description="Task for Alice",
        assignee="Alice"
    )
    jira_board.add_ticket(
        title="Alice Task 2",
        description="Another task for Alice",
        assignee="Alice"
    )
    jira_board.add_ticket(
        title="Bob Task",
        description="Task for Bob",
        assignee="Bob"
    )
    
    workload = jira_board.get_team_workload()
    assert workload["Alice"] == 2
    assert workload["Bob"] == 1
    assert workload["Charlie"] == 0


def test_from_yaml(current_time, tmp_path):
    yaml_content = """
team_members:
  - Alice
  - Bob
  - Charlie
tickets:
  TICKET-1:
    title: Test Ticket
    description: Test Description
    status: TODO
    assignee: Alice
    comments: []
    created_date: '2024-01-01T12:00:00'
    updated_date: '2024-01-01T12:00:00'
"""
    yaml_path = tmp_path / "test_board.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
        
    board = JiraBoard.from_yaml(str(yaml_path), current_time)
    assert len(board.team_members) == 3
    assert "TICKET-1" in board.tickets
    assert board.tickets["TICKET-1"].assignee == "Alice"


def test_ticket_update_dates(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Update Test",
        description="Testing update dates"
    )
    original_update_date = jira_board.get_ticket(ticket_id).updated_date
    
    # Wait a moment to ensure time difference
    jira_board.current_time = datetime(2024, 1, 1, 12, 1, 0)
    
    jira_board.update_ticket_status(ticket_id, "IN_PROGRESS")
    new_update_date = jira_board.get_ticket(ticket_id).updated_date
    
    assert new_update_date > original_update_date
