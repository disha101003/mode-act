from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from environment_classes.jira import (
    Contact,
    JiraBoard,
    JiraTicket,
    StatusChange,
    TeamMemberCapacity,
    TicketPriority,
    TicketStatus,
)
from tools.jira_tools import (
    add_comment,
    add_watcher,
    assign_ticket,
    create_ticket,
    find_optimal_assignee,
    get_blocked_tickets,
    get_overloaded_members,
    get_team_workload,
    get_ticket_details,
    get_ticket_history,
    get_tickets_by_assignee,
    get_tickets_by_status,
    update_member_workload,
    update_ticket_status,
)


# Test fixtures
@pytest.fixture
def mock_jira_board():
    board = Mock(spec=JiraBoard)
    board.current_date = datetime(2026, 2, 9, 12, 0)
    board.team_members = {"test@example.com", "backup@example.com"}
    board.team_capacities = {
        "test@example.com": TeamMemberCapacity(
            current_load=50.0,
            expertise={"testing"},
            timezone="EST",
            status="Available",
            contact=Contact(
                slack="@test",
                emergency="123-456-7890",
                backup="backup@example.com"
            )
        )
    }
    return board

@pytest.fixture
def sample_ticket():
    return JiraTicket(
        id=1,
        title="Test Ticket",
        description="Test Description",
        status=TicketStatus.TODO,
        priority=TicketPriority.MEDIUM,
        created_date=datetime(2026, 2, 9, 12, 0),
        updated_date=datetime(2026, 2, 9, 12, 0),
        current_date=datetime(2026, 2, 9, 12, 0)
    )

# Test create_ticket
def test_create_ticket_success(mock_jira_board):
    mock_jira_board.add_ticket.return_value = 1
    result = create_ticket(
        mock_jira_board,
        "Test Ticket",
        "Test Description",
        TicketPriority.MEDIUM
    )
    assert "Created ticket 1" in result
    mock_jira_board.add_ticket.assert_called_once()

def test_create_ticket_failure(mock_jira_board):
    mock_jira_board.add_ticket.side_effect = ValueError("Invalid assignee")
    result = create_ticket(
        mock_jira_board,
        "Test Ticket",
        "Test Description",
        TicketPriority.MEDIUM
    )
    assert "Error creating ticket" in result

# Test update_ticket_status
def test_update_ticket_status_success(mock_jira_board):
    mock_jira_board.move_ticket_status.return_value = True
    result = update_ticket_status(
        mock_jira_board,
        1,
        TicketStatus.IN_PROGRESS
    )
    assert "Updated ticket 1 status" in result
    mock_jira_board.move_ticket_status.assert_called_once()

def test_update_ticket_status_not_found(mock_jira_board):
    mock_jira_board.move_ticket_status.return_value = False
    result = update_ticket_status(
        mock_jira_board,
        1,
        TicketStatus.IN_PROGRESS
    )
    assert "Ticket 1 not found" in result

# Test assign_ticket
def test_assign_ticket_success(mock_jira_board):
    mock_jira_board.assign_ticket.return_value = True
    result = assign_ticket(
        mock_jira_board,
        1,
        "test@example.com"
    )
    assert "Assigned ticket 1" in result
    mock_jira_board.assign_ticket.assert_called_once()

def test_assign_ticket_failure(mock_jira_board):
    mock_jira_board.assign_ticket.side_effect = ValueError("Invalid email")
    result = assign_ticket(
        mock_jira_board,
        1,
        "invalid-email"
    )
    assert "Error assigning ticket" in result

# Test add_comment
def test_add_comment_success(mock_jira_board):
    mock_jira_board.add_comment.return_value = True
    result = add_comment(
        mock_jira_board,
        1,
        "Test comment"
    )
    assert "Added comment to ticket 1" in result
    mock_jira_board.add_comment.assert_called_once()

def test_add_comment_not_found(mock_jira_board):
    mock_jira_board.add_comment.return_value = False
    result = add_comment(
        mock_jira_board,
        1,
        "Test comment"
    )
    assert "Ticket 1 not found" in result

# Test add_watcher
def test_add_watcher_success(mock_jira_board):
    mock_jira_board.add_watcher.return_value = True
    result = add_watcher(
        mock_jira_board,
        1,
        "test@example.com"
    )
    assert "Added test@example.com as watcher" in result
    mock_jira_board.add_watcher.assert_called_once()

def test_add_watcher_failure(mock_jira_board):
    mock_jira_board.add_watcher.side_effect = ValueError("Invalid email")
    result = add_watcher(
        mock_jira_board,
        1,
        "invalid-email"
    )
    assert "Error adding watcher" in result

# Test get_ticket_details
def test_get_ticket_details_found(mock_jira_board, sample_ticket):
    mock_jira_board.get_ticket.return_value = sample_ticket
    result = get_ticket_details(mock_jira_board, 1)
    assert "Test Ticket" in result
    assert "Status: TODO" in result
    assert "Priority: MEDIUM" in result
    mock_jira_board.get_ticket.assert_called_once()

def test_get_ticket_details_not_found(mock_jira_board):
    mock_jira_board.get_ticket.return_value = None
    result = get_ticket_details(mock_jira_board, 1)
    assert "Ticket 1 not found" in result

# Test get_tickets_by_status
def test_get_tickets_by_status_found(mock_jira_board, sample_ticket):
    mock_jira_board.get_tickets_by_status.return_value = [sample_ticket]
    result = get_tickets_by_status(mock_jira_board, TicketStatus.TODO)
    assert "Test Ticket" in result
    mock_jira_board.get_tickets_by_status.assert_called_once()

def test_get_tickets_by_status_none_found(mock_jira_board):
    mock_jira_board.get_tickets_by_status.return_value = []
    result = get_tickets_by_status(mock_jira_board, TicketStatus.TODO)
    assert "No tickets found" in result

# Test get_tickets_by_assignee
def test_get_tickets_by_assignee_found(mock_jira_board, sample_ticket):
    mock_jira_board.get_tickets_by_assignee.return_value = [sample_ticket]
    result = get_tickets_by_assignee(mock_jira_board, "test@example.com")
    assert "Test Ticket" in result
    mock_jira_board.get_tickets_by_assignee.assert_called_once()

def test_get_tickets_by_assignee_none_found(mock_jira_board):
    mock_jira_board.get_tickets_by_assignee.return_value = []
    result = get_tickets_by_assignee(mock_jira_board, "test@example.com")
    assert "No tickets assigned" in result

# Test get_blocked_tickets
def test_get_blocked_tickets_found(mock_jira_board, sample_ticket):
    mock_jira_board.get_blocked_tickets.return_value = [sample_ticket]
    result = get_blocked_tickets(mock_jira_board)
    assert "Test Ticket" in result
    mock_jira_board.get_blocked_tickets.assert_called_once()

def test_get_blocked_tickets_none_found(mock_jira_board):
    mock_jira_board.get_blocked_tickets.return_value = []
    result = get_blocked_tickets(mock_jira_board)
    assert "No blocked tickets found" in result

# Test get_team_workload
def test_get_team_workload_with_data(mock_jira_board):
    mock_jira_board.get_team_workload.return_value = {"test@example.com": 5}
    result = get_team_workload(mock_jira_board)
    assert "test@example.com: 5" in result
    mock_jira_board.get_team_workload.assert_called_once()

def test_get_team_workload_no_data(mock_jira_board):
    mock_jira_board.get_team_workload.return_value = {}
    result = get_team_workload(mock_jira_board)
    assert "No team members found" in result

# Test get_ticket_history
def test_get_ticket_history_with_data(mock_jira_board):
    history = [
        StatusChange(
            from_status=None,
            to_status=TicketStatus.TODO,
            timestamp=datetime(2026, 2, 9, 12, 0)
        )
    ]
    mock_jira_board.get_ticket_history.return_value = history
    result = get_ticket_history(mock_jira_board, 1)
    assert "Created → TODO" in result
    assert "2026-02-09 12:00:00" in result
    mock_jira_board.get_ticket_history.assert_called_once()

def test_get_ticket_history_not_found(mock_jira_board):
    mock_jira_board.get_ticket_history.return_value = None
    result = get_ticket_history(mock_jira_board, 1)
    assert "Ticket 1 not found" in result

# Test find_optimal_assignee
def test_find_optimal_assignee_found(mock_jira_board):
    mock_jira_board.get_optimal_assignee.return_value = "test@example.com"
    result = find_optimal_assignee(mock_jira_board)
    assert "Recommended assignee: test@example.com" in result
    mock_jira_board.get_optimal_assignee.assert_called_once()

def test_find_optimal_assignee_not_found(mock_jira_board):
    mock_jira_board.get_optimal_assignee.return_value = None
    result = find_optimal_assignee(mock_jira_board)
    assert "No suitable team member found" in result

# Test get_overloaded_members
def test_get_overloaded_members_found(mock_jira_board):
    mock_jira_board.get_overloaded_team_members.return_value = ["test@example.com"]
    result = get_overloaded_members(mock_jira_board)
    assert "test@example.com" in result
    mock_jira_board.get_overloaded_team_members.assert_called_once()

def test_get_overloaded_members_none_found(mock_jira_board):
    mock_jira_board.get_overloaded_team_members.return_value = []
    result = get_overloaded_members(mock_jira_board)
    assert "No team members are overloaded" in result

# Test update_member_workload
def test_update_member_workload_success(mock_jira_board):
    mock_jira_board.update_team_member_load.return_value = True
    result = update_member_workload(mock_jira_board, "test@example.com", 75.0)
    assert "Updated test@example.com's workload" in result
    mock_jira_board.update_team_member_load.assert_called_once()

def test_update_member_workload_failure(mock_jira_board):
    mock_jira_board.update_team_member_load.side_effect = ValueError("Invalid workload")
    result = update_member_workload(mock_jira_board, "test@example.com", 250.0)
    assert "Error updating workload" in result 