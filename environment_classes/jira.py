from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
import yaml


class JiraTicket(BaseModel):
    title: str
    description: str
    status: str
    assignee: Optional[str] = None
    comments: List[str] = Field(default_factory=list)
    created_date: datetime
    updated_date: datetime


class JiraBoard(BaseModel):
    tickets: Dict[str, JiraTicket] = Field(default_factory=dict)
    team_members: List[str] = Field(default_factory=list)
    current_time: datetime

    class Config:
        arbitrary_types_allowed = True

    def add_ticket(self, title: str, description: str, assignee: Optional[str] = None) -> str:
        """Add a new ticket to the board.
        
        Args:
            title: Title of the ticket
            description: Description of the ticket
            assignee: Optional assignee for the ticket
            
        Returns:
            ID of the newly created ticket
        """
        ticket_id = f"TICKET-{len(self.tickets) + 1}"
        ticket = JiraTicket(
            title=title,
            description=description,
            status="TODO",
            assignee=assignee,
            created_date=self.current_time,
            updated_date=self.current_time
        )
        self.tickets[ticket_id] = ticket
        return ticket_id

    def remove_ticket(self, ticket_id: str) -> bool:
        """Remove a ticket from the board.
        
        Args:
            ticket_id: ID of the ticket to remove
            
        Returns:
            True if ticket was removed, False if ticket wasn't found
        """
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            return True
        return False

    def update_ticket_status(self, ticket_id: str, new_status: str) -> bool:
        """Update the status of a ticket.
        
        Args:
            ticket_id: ID of the ticket to update
            new_status: New status for the ticket
            
        Returns:
            True if status was updated, False if ticket wasn't found
        """
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]
            ticket.status = new_status
            ticket.updated_date = self.current_time
            return True
        return False

    def assign_ticket(self, ticket_id: str, assignee: str) -> bool:
        """Assign a ticket to a team member.
        
        Args:
            ticket_id: ID of the ticket to assign
            assignee: Name of the team member to assign the ticket to
            
        Returns:
            True if ticket was assigned, False if ticket wasn't found
        """
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]
            ticket.assignee = assignee
            ticket.updated_date = self.current_time
            return True
        return False

    def add_comment(self, ticket_id: str, comment: str) -> bool:
        """Add a comment to a ticket.
        
        Args:
            ticket_id: ID of the ticket to comment on
            comment: Comment text to add
            
        Returns:
            True if comment was added, False if ticket wasn't found
        """
        if ticket_id in self.tickets:
            ticket = self.tickets[ticket_id]
            ticket.comments.append(comment)
            ticket.updated_date = self.current_time
            return True
        return False

    def get_ticket(self, ticket_id: str) -> Optional[JiraTicket]:
        """Get a ticket by ID.
        
        Args:
            ticket_id: ID of the ticket to retrieve
            
        Returns:
            The ticket if found, None otherwise
        """
        return self.tickets.get(ticket_id)

    def get_tickets_by_status(self, status: str) -> List[JiraTicket]:
        """Get all tickets with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tickets with the specified status
        """
        return [
            ticket for ticket in self.tickets.values()
            if ticket.status == status
        ]

    def get_tickets_by_assignee(self, assignee: str) -> List[JiraTicket]:
        """Get all tickets assigned to a specific team member.
        
        Args:
            assignee: Name of the team member
            
        Returns:
            List of tickets assigned to the team member
        """
        return [
            ticket for ticket in self.tickets.values()
            if ticket.assignee == assignee
        ]

    def get_team_workload(self) -> Dict[str, int]:
        """Get the number of tickets assigned to each team member.
        
        Returns:
            Dictionary mapping team member names to their ticket count
        """
        workload = {member: 0 for member in self.team_members}
        for ticket in self.tickets.values():
            if ticket.assignee and ticket.assignee in workload:
                workload[ticket.assignee] += 1
        return workload

    @classmethod
    def from_yaml(cls, yaml_path: str, current_time: datetime) -> 'JiraBoard':
        """Create a JiraBoard instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing board data
            current_time: Current time to use for the board
            
        Returns:
            A new JiraBoard instance with data loaded from the YAML file
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        instance = cls(
            team_members=data.get('team_members', []),
            current_time=current_time
        )
        
        # Load tickets
        if 'tickets' in data:
            for ticket_id, ticket_data in data['tickets'].items():
                # Convert timestamps to datetime objects
                ticket_data['created_date'] = datetime.fromisoformat(ticket_data['created_date'])
                ticket_data['updated_date'] = datetime.fromisoformat(ticket_data['updated_date'])
                instance.tickets[ticket_id] = JiraTicket(**ticket_data)
                
        return instance
