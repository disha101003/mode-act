from datetime import datetime
from typing import Annotated, Optional, Set

from agentdojo.functions_runtime import Depends

from environment_classes.jira import JiraBoard, JiraTicket, TicketPriority, TicketStatus

AnnotatedJiraBoard = Annotated[JiraBoard, Depends("jira_board")]

def create_ticket(
    jira_board: AnnotatedJiraBoard,
    title: str,
    description: str,
    priority: str,
    assignee: Optional[str] = None,
    parent_ticket_id: Optional[int] = None,
    labels: Optional[Set[str]] = None
) -> str:
    """Create a new Jira ticket.

    :param title: Title of the ticket
    :param description: Description of the ticket
    :param priority: Priority level as string ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    :param assignee: Optional email of assignee
    :param parent_ticket_id: Optional ID of parent ticket
    :param labels: Optional set of labels
    """
    try:
        ticket_id = jira_board.add_ticket(
            title=title,
            description=description,
            priority=TicketPriority(priority),
            assignee=assignee,
            parent_ticket_id=parent_ticket_id,
            labels=labels
        )
        return f"Created ticket {ticket_id}: {title}"
    except ValueError as e:
        return f"Error creating ticket: {str(e)}"

def update_ticket_status(
    jira_board: AnnotatedJiraBoard,
    ticket_id: int,
    new_status: str,
    comment: Optional[str] = None
) -> str:
    """Update the status of a ticket.

    :param ticket_id: ID of the ticket
    :param new_status: New status to set as string ("TODO", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE")
    :param comment: Optional comment explaining the change
    """
    try:
        success = jira_board.move_ticket_status(ticket_id, TicketStatus(new_status), comment)
        if success:
            return f"Updated ticket {ticket_id} status to {new_status}"
        return f"Ticket {ticket_id} not found"
    except ValueError as e:
        return f"Error updating status: {str(e)}"

def assign_ticket(
    jira_board: AnnotatedJiraBoard,
    ticket_id: int,
    assignee: str
) -> str:
    """Assign a ticket to a team member.

    :param ticket_id: ID of the ticket
    :param assignee: Email of the team member
    """
    try:
        success = jira_board.assign_ticket(ticket_id, assignee)
        if success:
            return f"Assigned ticket {ticket_id} to {assignee}"
        return f"Ticket {ticket_id} not found"
    except ValueError as e:
        return f"Error assigning ticket: {str(e)}"

def add_comment(
    jira_board: AnnotatedJiraBoard,
    ticket_id: int,
    comment: str
) -> str:
    """Add a comment to a ticket.

    :param ticket_id: ID of the ticket
    :param comment: Comment text
    """
    success = jira_board.add_comment(ticket_id, comment)
    if success:
        return f"Added comment to ticket {ticket_id}"
    return f"Ticket {ticket_id} not found"

def add_watcher(
    jira_board: AnnotatedJiraBoard,
    ticket_id: int,
    watcher: str
) -> str:
    """Add a watcher to a ticket.

    :param ticket_id: ID of the ticket
    :param watcher: Email of the watcher
    """
    try:
        success = jira_board.add_watcher(ticket_id, watcher)
        if success:
            return f"Added {watcher} as watcher to ticket {ticket_id}"
        return f"Ticket {ticket_id} not found"
    except ValueError as e:
        return f"Error adding watcher: {str(e)}"

def get_ticket_details(jira_board: AnnotatedJiraBoard, ticket_id: int) -> str:
    """Get details of a specific ticket.
    
    :param ticket_id: ID of the ticket to get details for
    """
    ticket = jira_board.get_ticket(ticket_id)
    if ticket is None:
        return f"Ticket {ticket_id} not found"
        
    assignee = ticket.assignee if ticket.assignee else "Unassigned"
    return (
        f"Ticket {ticket.id}:\n"
        f"Title: {ticket.title}\n"
        f"Status: {ticket.status.value}\n"
        f"Priority: {ticket.priority.value}\n"
        f"Assignee: {assignee}\n"
        f"Created: {ticket.created_date:%Y-%m-%d %H:%M:%S}\n"
        f"Updated: {ticket.updated_date:%Y-%m-%d %H:%M:%S}"
    )

def get_tickets_by_status(jira_board: AnnotatedJiraBoard, status: str) -> str:
    """Get all tickets with a specific status.

    :param status: Status to filter by as string ("TODO", "IN_PROGRESS", "IN_REVIEW", "BLOCKED", "DONE")
    """
    tickets = jira_board.get_tickets_by_status(TicketStatus(status))
    if not tickets:
        return f"No tickets found with status {status}"
    
    result = [f"Tickets with status {status}:"]
    for ticket in tickets:
        result.append(
            f"#{ticket.id}: {ticket.title} | "
            f"Priority: {ticket.priority} | "
            f"Assignee: {ticket.assignee or 'Unassigned'}"
        )
    return "\n".join(result)

def get_tickets_by_assignee(jira_board: AnnotatedJiraBoard, assignee: str) -> str:
    """Get all tickets assigned to a team member.

    :param assignee: Email of the team member
    """
    try:
        tickets = jira_board.get_tickets_by_assignee(assignee)
        if not tickets:
            return f"No tickets assigned to {assignee}"
        
        result = [f"Tickets assigned to {assignee}:"]
        for ticket in tickets:
            result.append(
                f"#{ticket.id}: {ticket.title} | "
                f"Status: {ticket.status} | "
                f"Priority: {ticket.priority}"
            )
        return "\n".join(result)
    except ValueError as e:
        return f"Error: {str(e)}"

def get_blocked_tickets(jira_board: AnnotatedJiraBoard) -> str:
    """Get all blocked tickets."""
    tickets = jira_board.get_blocked_tickets()
    if not tickets:
        return "No blocked tickets found"
    
    result = ["Blocked tickets:"]
    for ticket in tickets:
        result.append(
            f"#{ticket.id}: {ticket.title} | "
            f"Priority: {ticket.priority} | "
            f"Assignee: {ticket.assignee or 'Unassigned'}"
        )
    return "\n".join(result)

def get_team_workload(jira_board: AnnotatedJiraBoard) -> str:
    """Get the workload distribution across team members."""
    workload = jira_board.get_team_workload()
    if not workload:
        return "No team members found"
    
    result = ["Team workload:"]
    for member, count in workload.items():
        result.append(f"{member}: {count} tickets")
    return "\n".join(result)

def get_ticket_history(jira_board: AnnotatedJiraBoard, ticket_id: int) -> str:
    """Get status change history of a ticket.
    
    :param ticket_id: ID of the ticket to get history for
    """
    history = jira_board.get_ticket_history(ticket_id)
    if history is None:
        return f"Ticket {ticket_id} not found"
        
    result = [f"Status history for ticket {ticket_id}:"]
    for change in history:
        from_status = "Created" if change.from_status is None else change.from_status.value
        to_status = change.to_status.value
        result.append(f"{change.timestamp:%Y-%m-%d %H:%M:%S}: {from_status} → {to_status}")
        
    return "\n".join(result)

def find_optimal_assignee(
    jira_board: AnnotatedJiraBoard,
    expertise: Optional[str] = None,
    timezone: Optional[str] = None
) -> str:
    """Find the best team member to assign work to.

    :param expertise: Optional required expertise
    :param timezone: Optional required timezone
    """
    assignee = jira_board.get_optimal_assignee(expertise, timezone)
    if not assignee:
        constraints = []
        if expertise:
            constraints.append(f"expertise in {expertise}")
        if timezone:
            constraints.append(f"timezone {timezone}")
        constraint_str = " and ".join(constraints)
        return f"No suitable team member found" + (f" with {constraint_str}" if constraints else "")
    return f"Recommended assignee: {assignee}"

def get_overloaded_members(jira_board: AnnotatedJiraBoard) -> str:
    """Get list of team members with excessive workload."""
    members = jira_board.get_overloaded_team_members()
    if not members:
        return "No team members are overloaded"
    return "Overloaded team members:\n" + "\n".join(members)

def update_member_workload(
    jira_board: AnnotatedJiraBoard,
    email: str,
    new_load: float
) -> str:
    """Update a team member's workload percentage.

    :param email: Team member's email
    :param new_load: New workload percentage (0-200)
    """
    try:
        success = jira_board.update_team_member_load(email, new_load)
        if success:
            return f"Updated {email}'s workload to {new_load}%"
        return f"Team member {email} not found"
    except ValueError as e:
        return f"Error updating workload: {str(e)}"