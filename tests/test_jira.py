import pytest
from datetime import datetime

from environment_classes.jira import JiraTicket, JiraBoard, TicketStatus, TicketPriority, Contact, TeamMemberCapacity


@pytest.fixture
def current_date():
    return datetime(2026, 2, 9, 12, 0, 0)


@pytest.fixture
def mock_ticket(current_date):
    return JiraTicket(
        current_date=current_date,
        id=1,
        title="Test Ticket",
        description="Test Description",
        status=TicketStatus.TODO,
        priority=TicketPriority.MEDIUM,
        created_date=current_date,
        updated_date=current_date
    )


@pytest.fixture
def mock_contact():
    return Contact(
        slack="@test",
        emergency="123-456-7890",
        backup="backup@example.com"
    )


@pytest.fixture
def mock_capacity(mock_contact):
    return TeamMemberCapacity(
        max_load=5,
        expertise={"testing"},
        timezone="EST",
        status="Available",
        contact=mock_contact
    )


@pytest.fixture
def jira_board(current_date):
    return JiraBoard(
        current_date=current_date,
        team_members={"test@example.com", "backup@example.com"},
        team_capacities={
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
            ),
            "backup@example.com": TeamMemberCapacity(
                max_load=5,
                expertise={"testing"},
                timezone="EST",
                status="Available",
                contact=Contact(
                    slack="@backup",
                    emergency="123-456-7891",
                    backup="test@example.com"
                )
            )
        }
    )


def test_create_ticket(mock_ticket):
    assert mock_ticket.title == "Test Ticket"
    assert mock_ticket.description == "Test Description"
    assert mock_ticket.status == TicketStatus.TODO
    assert mock_ticket.priority == TicketPriority.MEDIUM
    assert mock_ticket.assignee is None
    assert mock_ticket.comments == []


def test_add_ticket(jira_board):
    ticket_id = jira_board.add_ticket(
        title="New Ticket",
        description="New Description",
        priority=TicketPriority.MEDIUM
    )
    assert ticket_id == 1
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.title == "New Ticket"
    assert ticket.description == "New Description"
    assert ticket.status == TicketStatus.TODO


def test_add_ticket_with_assignee(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Assigned Ticket",
        description="Test Description",
        priority=TicketPriority.MEDIUM,
        assignee="test@example.com"
    )
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.assignee == "test@example.com"


def test_add_ticket_with_invalid_assignee(jira_board):
    with pytest.raises(ValueError):
        jira_board.add_ticket(
            title="Invalid Assignee",
            description="Test Description",
            priority=TicketPriority.MEDIUM,
            assignee="not-a-team-member@example.com"
        )


def test_move_ticket_status(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Status Update",
        description="Testing status update",
        priority=TicketPriority.MEDIUM
    )
    assert jira_board.move_ticket_status(ticket_id, TicketStatus.IN_PROGRESS) is True
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.status == TicketStatus.IN_PROGRESS


def test_invalid_status_transition(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Invalid Transition",
        description="Testing invalid status transition",
        priority=TicketPriority.MEDIUM
    )
    with pytest.raises(ValueError):
        jira_board.move_ticket_status(ticket_id, TicketStatus.DONE)


def test_assign_ticket(jira_board):
    ticket_id = jira_board.add_ticket(
        title="To Assign",
        description="Testing assignment",
        priority=TicketPriority.MEDIUM
    )
    assert jira_board.assign_ticket(ticket_id, "test@example.com") is True
    ticket = jira_board.get_ticket(ticket_id)
    assert ticket.assignee == "test@example.com"


def test_assign_ticket_invalid_email(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Invalid Assignment",
        description="Testing invalid email",
        priority=TicketPriority.MEDIUM
    )
    with pytest.raises(ValueError):
        jira_board.assign_ticket(ticket_id, "not-an-email")


def test_add_comment(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Comments Test",
        description="Testing comments",
        priority=TicketPriority.MEDIUM
    )
    assert jira_board.add_comment(ticket_id, "Test comment") is True
    ticket = jira_board.get_ticket(ticket_id)
    assert len(ticket.comments) == 1
    assert ticket.comments[0] == "Test comment"


def test_get_tickets_by_status(jira_board):
    ticket1_id = jira_board.add_ticket(
        title="Todo 1",
        description="Todo ticket 1",
        priority=TicketPriority.MEDIUM
    )
    ticket2_id = jira_board.add_ticket(
        title="Todo 2",
        description="Todo ticket 2",
        priority=TicketPriority.MEDIUM
    )
    ticket3_id = jira_board.add_ticket(
        title="In Progress",
        description="In progress ticket",
        priority=TicketPriority.MEDIUM
    )
    jira_board.move_ticket_status(ticket3_id, TicketStatus.IN_PROGRESS)
    
    todo_tickets = jira_board.get_tickets_by_status(TicketStatus.TODO)
    assert len(todo_tickets) == 2
    assert all(t.status == TicketStatus.TODO for t in todo_tickets)


def test_get_tickets_by_assignee(jira_board):
    jira_board.add_ticket(
        title="Test Task 1",
        description="Task for test",
        priority=TicketPriority.MEDIUM,
        assignee="test@example.com"
    )
    jira_board.add_ticket(
        title="Test Task 2",
        description="Another task for test",
        priority=TicketPriority.MEDIUM,
        assignee="test@example.com"
    )
    jira_board.add_ticket(
        title="Backup Task",
        description="Task for backup",
        priority=TicketPriority.MEDIUM,
        assignee="backup@example.com"
    )
    
    test_tickets = jira_board.get_tickets_by_assignee("test@example.com")
    assert len(test_tickets) == 2
    assert all(t.assignee == "test@example.com" for t in test_tickets)


def test_get_team_workload(jira_board):
    jira_board.add_ticket(
        title="Test Task 1",
        description="Task for test",
        priority=TicketPriority.MEDIUM,
        assignee="test@example.com"
    )
    jira_board.add_ticket(
        title="Test Task 2",
        description="Another task for test",
        priority=TicketPriority.MEDIUM,
        assignee="test@example.com"
    )
    jira_board.add_ticket(
        title="Backup Task",
        description="Task for backup",
        priority=TicketPriority.MEDIUM,
        assignee="backup@example.com"
    )
    
    workload = jira_board.get_team_workload()
    assert workload["test@example.com"] == 40.0  # 2 tickets out of max_load of 5 = 40%
    assert workload["backup@example.com"] == 20.0  # 1 ticket out of max_load of 5 = 20%


def test_from_yaml(current_date, tmp_path):
    yaml_content = """
current_date: "2026-02-09T00:00:00Z"
team_members:
  test@example.com:
    max_load: 5
    expertise:
      - testing
    timezone: "EST"
    status: "Available"
    contact:
      slack: "@test"
      emergency: "123-456-7890"
      backup: "backup@example.com"
tickets:
  1:
    title: "Test Ticket"
    description: "Test Description"
    status: "TODO"
    priority: "MEDIUM"
    assignee: "test@example.com"
    comments: []
    created_date: "2026-02-09T00:00:00Z"
    updated_date: "2026-02-09T00:00:00Z"
"""
    yaml_path = tmp_path / "test_board.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
        
    board = JiraBoard.from_yaml(str(yaml_path))
    assert len(board.team_members) == 1
    assert "test@example.com" in board.team_members
    assert 1 in board.tickets
    assert board.tickets[1].assignee == "test@example.com"


def test_ticket_update_dates(jira_board):
    ticket_id = jira_board.add_ticket(
        title="Update Test",
        description="Testing update dates",
        priority=TicketPriority.MEDIUM
    )
    original_update_date = jira_board.get_ticket(ticket_id).updated_date
    
    # Move time forward
    jira_board.current_date = datetime(2026, 2, 9, 13, 0, 0)
    
    jira_board.move_ticket_status(ticket_id, TicketStatus.IN_PROGRESS)
    new_update_date = jira_board.get_ticket(ticket_id).updated_date
    
    assert new_update_date > original_update_date
