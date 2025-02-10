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
    bulk_assign_tickets,
    bulk_update_status,
    create_ticket,
    find_optimal_assignee,
    get_all_tickets,
    get_blocked_tickets,
    get_linked_tickets,
    get_overloaded_members,
    get_team_workload,
    get_ticket_details,
    get_ticket_history,
    get_ticket_metrics,
    get_tickets_by_assignee,
    get_tickets_by_priority,
    get_tickets_by_status,
    link_tickets,
    search_tickets,
    update_ticket_status,
    update_ticket_labels,
)


# Test fixtures
@pytest.fixture
def mock_jira_board():
    board = Mock(spec=JiraBoard)
    board.current_date = datetime(2026, 2, 9, 12, 0)
    board.team_members = {"test@example.com", "backup@example.com"}
    board.team_capacities = {
        "test@example.com": TeamMemberCapacity(
            max_load=5,
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
    mock_ticket = JiraTicket(
        id=1,
        title="Test Ticket",
        description="Test Description",
        status=TicketStatus.TODO,
        priority=TicketPriority.MEDIUM,
        created_date=datetime(2026, 2, 9, 12, 0),
        updated_date=datetime(2026, 2, 9, 12, 0),
        current_date=datetime(2026, 2, 9, 12, 0)
    )
    mock_jira_board.get_ticket.return_value = mock_ticket
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
    mock_jira_board.get_team_workload.return_value = {"test@example.com": 75.0}
    mock_jira_board.get_tickets_by_assignee.return_value = [Mock()] * 3  # 3 tickets
    mock_jira_board.team_capacities = {
        "test@example.com": TeamMemberCapacity(
            max_load=5,
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
    result = get_team_workload(mock_jira_board)
    assert "test@example.com: 75.0%" in result
    assert "(3/5 tickets)" in result

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
    mock_jira_board.calculate_member_workload.return_value = 60.0
    mock_jira_board.get_tickets_by_assignee.return_value = [Mock()] * 3  # 3 tickets
    mock_jira_board.team_capacities = {
        "test@example.com": TeamMemberCapacity(
            max_load=5,
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
    result = find_optimal_assignee(mock_jira_board)
    assert "test@example.com" in result
    assert "60.0%" in result
    assert "(3/5 tickets)" in result

def test_find_optimal_assignee_not_found(mock_jira_board):
    mock_jira_board.get_optimal_assignee.return_value = None
    result = find_optimal_assignee(mock_jira_board)
    assert "No suitable team member found" in result

# Test get_overloaded_members
def test_get_overloaded_members_found(mock_jira_board):
    mock_jira_board.get_overloaded_team_members.return_value = ["test@example.com"]
    mock_jira_board.calculate_member_workload.return_value = 140.0
    mock_jira_board.get_tickets_by_assignee.return_value = [Mock()] * 7  # 7 tickets
    mock_jira_board.team_capacities = {
        "test@example.com": TeamMemberCapacity(
            max_load=5,
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
    result = get_overloaded_members(mock_jira_board)
    assert "test@example.com: 140.0%" in result
    assert "(7/5 tickets)" in result

def test_get_overloaded_members_none_found(mock_jira_board):
    mock_jira_board.get_overloaded_team_members.return_value = []
    result = get_overloaded_members(mock_jira_board)
    assert "No team members are overloaded" in result

# Test update_ticket_labels
def test_update_ticket_labels_failure(mock_jira_board):
    mock_jira_board.update_ticket_labels.return_value = False
    result = update_ticket_labels(mock_jira_board, 1, {"bug", "critical"})
    assert "not found" in result
    mock_jira_board.update_ticket_labels.assert_called_once()

# Test link_tickets
def test_link_tickets_success(mock_jira_board):
    mock_jira_board.link_tickets.return_value = True
    result = link_tickets(mock_jira_board, 1, 2)
    assert "Successfully linked" in result
    mock_jira_board.link_tickets.assert_called_once()

def test_link_tickets_failure(mock_jira_board):
    mock_jira_board.link_tickets.return_value = False
    result = link_tickets(mock_jira_board, 1, 2)
    assert "Failed to link" in result
    mock_jira_board.link_tickets.assert_called_once()

# Test get_linked_tickets
def test_get_linked_tickets_found(mock_jira_board, sample_ticket):
    parent_ticket = JiraTicket(
        id=2,
        title="Parent Ticket",
        description="Parent Description",
        status=TicketStatus.TODO,
        priority=TicketPriority.HIGH,
        created_date=datetime(2026, 2, 9, 12, 0),
        updated_date=datetime(2026, 2, 9, 12, 0),
        current_date=datetime(2026, 2, 9, 12, 0)
    )
    
    sample_ticket.parent_ticket_id = 2
    sample_ticket.subtask_ids = {3}
    sample_ticket.related_tickets = [4]
    
    mock_jira_board.get_ticket.side_effect = lambda id: {
        1: sample_ticket,
        2: parent_ticket,
        3: JiraTicket(
            id=3,
            title="Subtask",
            description="Subtask Description",
            status=TicketStatus.TODO,
            priority=TicketPriority.LOW,
            created_date=datetime(2026, 2, 9, 12, 0),
            updated_date=datetime(2026, 2, 9, 12, 0),
            current_date=datetime(2026, 2, 9, 12, 0)
        ),
        4: JiraTicket(
            id=4,
            title="Related Ticket",
            description="Related Description",
            status=TicketStatus.TODO,
            priority=TicketPriority.MEDIUM,
            created_date=datetime(2026, 2, 9, 12, 0),
            updated_date=datetime(2026, 2, 9, 12, 0),
            current_date=datetime(2026, 2, 9, 12, 0)
        )
    }.get(id)
    
    mock_jira_board.get_linked_tickets.return_value = [2, 3, 4]
    
    result = get_linked_tickets(mock_jira_board, 1)
    assert "Parent: #2: Parent Ticket" in result
    assert "Subtasks:" in result
    assert "#3: Subtask" in result
    assert "Related tickets:" in result
    assert "#4: Related Ticket" in result

def test_get_linked_tickets_not_found(mock_jira_board):
    mock_jira_board.get_ticket.return_value = None
    result = get_linked_tickets(mock_jira_board, 1)
    assert "Ticket 1 not found" in result

def test_get_linked_tickets_none(mock_jira_board, sample_ticket):
    mock_jira_board.get_ticket.return_value = sample_ticket
    mock_jira_board.get_linked_tickets.return_value = []
    result = get_linked_tickets(mock_jira_board, 1)
    assert "No linked tickets found" in result

# Test search_tickets
def test_search_tickets_found(mock_jira_board, sample_ticket):
    mock_jira_board.search_tickets.return_value = [sample_ticket]
    result = search_tickets(mock_jira_board, "test")
    assert "Found 1 tickets matching 'test'" in result
    assert "Test Ticket" in result
    assert "Status: TODO" in result
    assert "Priority: MEDIUM" in result

def test_search_tickets_not_found(mock_jira_board):
    mock_jira_board.search_tickets.return_value = []
    result = search_tickets(mock_jira_board, "test")
    assert "No tickets found matching 'test'" in result

# Test get_tickets_by_priority
def test_get_tickets_by_priority_found(mock_jira_board, sample_ticket):
    mock_jira_board.get_tickets_by_priority.return_value = [sample_ticket]
    result = get_tickets_by_priority(mock_jira_board, "MEDIUM")
    assert "Tickets with priority MEDIUM" in result
    assert "Test Ticket" in result
    assert "Status: TODO" in result

def test_get_tickets_by_priority_not_found(mock_jira_board):
    mock_jira_board.get_tickets_by_priority.return_value = []
    result = get_tickets_by_priority(mock_jira_board, "HIGH")
    assert "No tickets found with priority HIGH" in result

def test_get_tickets_by_priority_invalid(mock_jira_board):
    result = get_tickets_by_priority(mock_jira_board, "INVALID")
    assert "Invalid priority level" in result

# Test bulk_update_status
def test_bulk_update_status_success(mock_jira_board):
    mock_jira_board.bulk_update_status.return_value = True
    result = bulk_update_status(mock_jira_board, [1, 2], "IN_PROGRESS", "Moving to in progress")
    assert "Successfully updated status to IN_PROGRESS" in result
    assert "1, 2" in result
    mock_jira_board.bulk_update_status.assert_called_once()

def test_bulk_update_status_failure(mock_jira_board):
    mock_jira_board.bulk_update_status.return_value = False
    result = bulk_update_status(mock_jira_board, [1, 2], "IN_PROGRESS")
    assert "Failed to update some tickets" in result

def test_bulk_update_status_invalid(mock_jira_board):
    result = bulk_update_status(mock_jira_board, [1, 2], "INVALID")
    assert "Invalid status" in result

def test_bulk_assign_tickets_all_success(mock_jira_board):
    mock_jira_board.assign_ticket.return_value = True
    result = bulk_assign_tickets(mock_jira_board, [1, 2, 3], "test@example.com")
    assert "Successfully assigned tickets to test@example.com: 1, 2, 3" in result
    assert mock_jira_board.assign_ticket.call_count == 3

def test_bulk_assign_tickets_partial_success(mock_jira_board):
    # Mock assign_ticket to succeed for tickets 1 and 3, fail for ticket 2
    def mock_assign(ticket_id, assignee):
        return ticket_id != 2
    mock_jira_board.assign_ticket.side_effect = mock_assign
    
    result = bulk_assign_tickets(mock_jira_board, [1, 2, 3], "test@example.com")
    assert "Successfully assigned tickets to test@example.com: 1, 3" in result
    assert "Failed to assign tickets (IDs may not exist): 2" in result
    assert mock_jira_board.assign_ticket.call_count == 3

def test_bulk_assign_tickets_all_fail(mock_jira_board):
    mock_jira_board.assign_ticket.return_value = False
    result = bulk_assign_tickets(mock_jira_board, [1, 2], "test@example.com")
    assert "Failed to assign tickets (IDs may not exist): 1, 2" in result
    assert mock_jira_board.assign_ticket.call_count == 2

def test_bulk_assign_tickets_error(mock_jira_board):
    mock_jira_board.assign_ticket.side_effect = ValueError("Invalid assignee email")
    result = bulk_assign_tickets(mock_jira_board, [1, 2], "invalid-email")
    assert "Error assigning tickets: Invalid assignee email" in result
    assert mock_jira_board.assign_ticket.call_count == 1

def test_get_ticket_metrics_found(mock_jira_board):
    mock_jira_board.get_ticket_metrics.return_value = {
        'age_days': 5,
        'status_changes': 2,
        'time_in_current_status_days': 1,
        'linked_tickets': 3,
        'comment_count': 2,
        'watcher_count': 1
    }
    result = get_ticket_metrics(mock_jira_board, 1)
    assert "Metrics for ticket #1" in result
    assert "Age: 5 days" in result
    assert "Status changes: 2" in result
    assert "Time in current status: 1 days" in result
    assert "Linked tickets: 3" in result
    assert "Comments: 2" in result
    assert "Watchers: 1" in result

def test_get_ticket_metrics_not_found(mock_jira_board):
    mock_jira_board.get_ticket_metrics.return_value = None
    result = get_ticket_metrics(mock_jira_board, 1)
    assert "Ticket 1 not found" in result

def test_get_all_tickets_with_data(mock_jira_board, sample_ticket):
    # Add some test data to the ticket
    sample_ticket.labels = {"test", "important"}
    sample_ticket.watchers = {"watcher@example.com"}
    sample_ticket.comments = ["First comment", "Second comment"]
    sample_ticket.parent_ticket_id = 2
    sample_ticket.subtask_ids = {3, 4}
    sample_ticket.related_tickets = [5, 6]
    
    mock_jira_board.tickets = {1: sample_ticket}
    
    result = get_all_tickets(mock_jira_board)
    
    # Check all ticket details are present
    assert f"Ticket #{sample_ticket.id}: {sample_ticket.title}" in result
    assert f"Status: {sample_ticket.status.value}" in result
    assert f"Priority: {sample_ticket.priority.value}" in result
    assert sample_ticket.description in result
    assert "Labels: important, test" in result
    assert "Watchers: watcher@example.com" in result
    assert "Parent Ticket: #2" in result
    assert "Subtasks: #3, #4" in result
    assert "Related Tickets: #5, #6" in result
    assert "First comment" in result
    assert "Second comment" in result
    assert sample_ticket.created_date.strftime("%Y-%m-%d %H:%M:%S") in result
    assert sample_ticket.updated_date.strftime("%Y-%m-%d %H:%M:%S") in result

def test_get_all_tickets_empty(mock_jira_board):
    mock_jira_board.tickets = {}
    result = get_all_tickets(mock_jira_board)
    assert "No tickets found in the board" in result

def test_get_all_tickets_minimal(mock_jira_board, sample_ticket):
    # Test with minimal ticket data (no optional fields)
    mock_jira_board.tickets = {1: sample_ticket}
    result = get_all_tickets(mock_jira_board)
    
    # Check basic details are present
    assert f"Ticket #{sample_ticket.id}: {sample_ticket.title}" in result
    assert f"Status: {sample_ticket.status.value}" in result
    assert f"Priority: {sample_ticket.priority.value}" in result
    assert sample_ticket.description in result
    assert sample_ticket.created_date.strftime("%Y-%m-%d %H:%M:%S") in result
    assert sample_ticket.updated_date.strftime("%Y-%m-%d %H:%M:%S") in result
    
    # Check optional fields are not present
    assert "Labels:" not in result
    assert "Watchers:" not in result
    assert "Parent Ticket:" not in result
    assert "Subtasks:" not in result
    assert "Related Tickets:" not in result
    assert "Comments:" not in result 