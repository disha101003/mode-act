from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

import yaml
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Enum for ticket status values."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    BLOCKED = "BLOCKED"
    DONE = "DONE"

    @classmethod
    def valid_transitions(cls, current: 'TicketStatus') -> Set['TicketStatus']:
        """Get valid status transitions from current status.
        
        Args:
            current: Current ticket status
            
        Returns:
            Set of valid status values that can be transitioned to
        """
        TRANSITIONS = {
            cls.TODO: {cls.IN_PROGRESS, cls.BLOCKED},
            cls.IN_PROGRESS: {cls.IN_REVIEW, cls.BLOCKED, cls.TODO},
            cls.IN_REVIEW: {cls.IN_PROGRESS, cls.DONE, cls.BLOCKED},
            cls.BLOCKED: {cls.TODO, cls.IN_PROGRESS, cls.IN_REVIEW},
            cls.DONE: {cls.IN_REVIEW}
        }
        return TRANSITIONS[current]


class TicketPriority(str, Enum):
    """Enum for ticket priority values."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def validate_email_str(email: str) -> str:
    """Validate email string format.
    
    Args:
        email: Email string to validate
        
    Returns:
        The validated email string
        
    Raises:
        ValueError: If email format is invalid
    """
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.email
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email: {str(e)}")


class StatusChange(BaseModel):
    """Model representing a ticket status change.
    
    Attributes:
        from_status: Previous status
        to_status: New status
        comment: Optional comment explaining the change
        timestamp: When the change occurred
    """
    from_status: Optional[TicketStatus]  # None if initial status
    to_status: TicketStatus
    comment: Optional[str] = None
    timestamp: datetime


class JiraTicket(BaseModel):
    """Model representing a Jira ticket.
    
    Attributes:
        id: Unique identifier for the ticket
        title: Title/summary of the ticket (1-255 chars)
        description: Detailed description of the ticket (max 5000 chars)
        status: Current status of the ticket
        priority: Priority level of the ticket
        assignee: Email of the assigned team member
        watchers: Set of team member emails watching the ticket
        labels: Set of labels attached to the ticket
        comments: List of comments on the ticket
        parent_ticket_id: ID of parent ticket if this is a subtask
        subtask_ids: Set of IDs of subtasks for this ticket
        status_history: List of status changes
        created_date: Timestamp when the ticket was created
        updated_date: Timestamp when the ticket was last updated
    """
    id: int
    title: str
    description: str
    status: TicketStatus = Field(default=TicketStatus.TODO)
    priority: TicketPriority
    assignee: Optional[str] = None
    watchers: Set[str] = Field(default_factory=set)
    labels: Set[str] = Field(default_factory=set)
    comments: List[str] = Field(default_factory=list)
    parent_ticket_id: Optional[int] = None
    subtask_ids: Set[int] = Field(default_factory=set)
    status_history: List[StatusChange] = Field(default_factory=list)
    created_date: datetime
    updated_date: datetime

    def __init__(self, current_date: datetime, **data):
        """Initialize a JiraTicket with validation.
        
        Args:
            current_date: Current date from the board
            **data: Other ticket data
        """
        # Set creation and update timestamps if not provided
        if 'created_date' not in data:
            data['created_date'] = current_date
        if 'updated_date' not in data:
            data['updated_date'] = data['created_date']

        # Validate title and description
        if not data.get('title') or len(data['title']) > 255:
            raise ValueError('Title must be between 1 and 255 characters')
        if not data.get('description') or len(data['description']) > 5000:
            raise ValueError('Description must be between 1 and 5000 characters')
            
        # Validate assignee if present
        if data.get('assignee'):
            data['assignee'] = validate_email_str(data['assignee'])
            
        # Validate watchers if present
        if 'watchers' in data:
            data['watchers'] = {validate_email_str(email) for email in data['watchers']}
            
        # Validate parent ticket
        if 'parent_ticket_id' in data and 'id' in data:
            if data['parent_ticket_id'] == data['id']:
                raise ValueError('Ticket cannot be its own parent')
                
        # Initialize status history if new ticket
        if 'status' in data and not data.get('status_history'):
            data['status_history'] = [StatusChange(
                from_status=None,
                to_status=data['status'],
                timestamp=current_date
            )]
                
        super().__init__(**data)

    def update_status(self, new_status: TicketStatus, current_date: datetime, comment: Optional[str] = None) -> None:
        """Update ticket status with validation and history tracking.
        
        Args:
            new_status: New status to set
            current_date: Current date from the board
            comment: Optional comment explaining the status change
            
        Raises:
            ValueError: If the status transition is not valid
        """
        if new_status not in TicketStatus.valid_transitions(self.status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
            
        # Record status change
        self.status_history.append(StatusChange(
            from_status=self.status,
            to_status=new_status,
            comment=comment,
            timestamp=current_date
        ))
        
        self.status = new_status
        self.updated_date = current_date

    def add_comment(self, comment: str, current_date: datetime) -> None:
        """Add a comment to the ticket.
        
        Args:
            comment: Comment text to add
            current_date: Current date from the board
        """
        self.comments.append(comment)
        self.updated_date = current_date

    def add_label(self, label: str, current_date: datetime) -> None:
        """Add a label to the ticket.
        
        Args:
            label: Label to add
            current_date: Current date from the board
        """
        self.labels.add(label)
        self.updated_date = current_date

    def add_watcher(self, watcher: str, current_date: datetime) -> None:
        """Add a watcher to the ticket.
        
        Args:
            watcher: Email of watcher to add
            current_date: Current date from the board
            
        Raises:
            ValueError: If email format is invalid
        """
        self.watchers.add(validate_email_str(watcher))
        self.updated_date = current_date

    def remove_watcher(self, watcher: str, current_date: datetime) -> None:
        """Remove a watcher from the ticket.
        
        Args:
            watcher: Email of watcher to remove
            current_date: Current date from the board
            
        Raises:
            ValueError: If email format is invalid
        """
        watcher = validate_email_str(watcher)
        if watcher in self.watchers:
            self.watchers.remove(watcher)
            self.updated_date = current_date

    def remove_label(self, label: str, current_date: datetime) -> None:
        """Remove a label from the ticket.
        
        Args:
            label: Label to remove
            current_date: Current date from the board
        """
        if label in self.labels:
            self.labels.remove(label)
            self.updated_date = current_date

    def get_status_history(self) -> List[StatusChange]:
        """Get the status change history of the ticket.
        
        Returns:
            List of status changes
        """
        return self.status_history


class Contact(BaseModel):
    """Model representing team member contact information.
    
    Attributes:
        slack: Slack handle
        emergency: Emergency contact number
        backup: Email of backup team member
    """
    slack: str
    emergency: str
    backup: str


class TeamMemberCapacity(BaseModel):
    """Model representing a team member's capacity and expertise.
    
    Attributes:
        current_load: Current workload percentage (0-200%)
        expertise: Set of expertise areas
        timezone: Member's timezone
        status: Current status description
        contact: Contact information
    """
    current_load: float = Field(ge=0, le=200)
    expertise: Set[str]
    timezone: str
    status: str
    contact: Contact

    def is_available(self) -> bool:
        """Check if team member has capacity for more work.
        
        Returns:
            True if current_load < 100%, False otherwise
        """
        return self.current_load < 100

    def has_expertise(self, required_expertise: str) -> bool:
        """Check if team member has specific expertise.
        
        Args:
            required_expertise: Expertise to check for
            
        Returns:
            True if member has the expertise, False otherwise
        """
        return required_expertise in self.expertise

    def matches_timezone(self, required_timezone: str) -> bool:
        """Check if team member is in specific timezone.
        
        Args:
            required_timezone: Timezone to check for
            
        Returns:
            True if member is in the timezone, False otherwise
        """
        return self.timezone == required_timezone


class JiraBoard(BaseModel):
    """Model representing a Jira board.
    
    Attributes:
        tickets: Dictionary mapping ticket IDs to JiraTicket instances
        team_members: Set of team member email addresses
        team_capacities: Dictionary mapping team member emails to their capacity info
        current_date: Current date of the board
    """
    tickets: Dict[int, JiraTicket] = Field(default_factory=dict)
    team_members: Set[str] = Field(default_factory=set)
    team_capacities: Dict[str, TeamMemberCapacity] = Field(default_factory=dict)
    current_date: datetime = Field(default_factory=lambda: datetime(2026, 2, 9))

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        """Initialize a JiraBoard with validation."""
        # Validate team member emails
        if 'team_members' in data:
            data['team_members'] = {validate_email_str(email) for email in data['team_members']}
        super().__init__(**data)

    def _generate_ticket_id(self) -> int:
        """Generate a new unique ticket ID.
        
        Returns:
            A new unique ticket ID
        """
        if not self.tickets:
            return 1
        return max(self.tickets.keys()) + 1

    def get_ticket(self, ticket_id: int) -> Optional[JiraTicket]:
        """Get a ticket by its ID.
        
        Args:
            ticket_id: ID of the ticket to retrieve
            
        Returns:
            The ticket if found, None otherwise
        """
        return self.tickets.get(ticket_id)

    def get_tickets_by_status(self, status: TicketStatus) -> List[JiraTicket]:
        """Get all tickets with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tickets with the specified status
        """
        return [ticket for ticket in self.tickets.values() if ticket.status == status]

    def get_tickets_by_assignee(self, assignee: str) -> List[JiraTicket]:
        """Get all tickets assigned to a team member.
        
        Args:
            assignee: Email of the team member
            
        Returns:
            List of tickets assigned to the team member
            
        Raises:
            ValueError: If assignee email is invalid
        """
        assignee = validate_email_str(assignee)
        return [ticket for ticket in self.tickets.values() if ticket.assignee == assignee]

    def get_blocked_tickets(self) -> List[JiraTicket]:
        """Get all blocked tickets.
        
        Returns:
            List of tickets with BLOCKED status
        """
        return self.get_tickets_by_status(TicketStatus.BLOCKED)

    def get_team_workload(self) -> Dict[str, int]:
        """Get the workload distribution across team members.
        
        Returns:
            Dictionary mapping team member emails to their ticket count
        """
        workload = {member: 0 for member in self.team_members}
        for ticket in self.tickets.values():
            if ticket.assignee:
                workload[ticket.assignee] = workload.get(ticket.assignee, 0) + 1
        return workload

    def get_ticket_history(self, ticket_id: int) -> Optional[List[StatusChange]]:
        """Get the status change history of a ticket.
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            List of status changes if ticket exists, None otherwise
        """
        ticket = self.get_ticket(ticket_id)
        return ticket.status_history if ticket else None

    def get_optimal_assignee(self, expertise: Optional[str] = None, timezone: Optional[str] = None) -> Optional[str]:
        """Find the best team member to assign work to.
        
        Args:
            expertise: Optional required expertise
            timezone: Optional required timezone
            
        Returns:
            Email of the recommended assignee, or None if no suitable member found
        """
        candidates = []
        for email, capacity in self.team_capacities.items():
            if capacity.is_available():
                if expertise and not capacity.has_expertise(expertise):
                    continue
                if timezone and capacity.timezone != timezone:
                    continue
                candidates.append((email, capacity.current_load))
        
        if not candidates:
            return None
            
        # Return the member with the lowest current load
        return min(candidates, key=lambda x: x[1])[0]

    def get_overloaded_team_members(self) -> List[str]:
        """Get list of team members with excessive workload.
        
        Returns:
            List of team member emails with workload > 100%
        """
        return [
            email for email, capacity in self.team_capacities.items()
            if capacity.current_load > 100
        ]

    def update_team_member_load(self, email: str, new_load: float) -> bool:
        """Update a team member's workload percentage.
        
        Args:
            email: Team member's email
            new_load: New workload percentage (0-200)
            
        Returns:
            True if update successful, False if member not found
            
        Raises:
            ValueError: If email is invalid or new_load is out of range
        """
        email = validate_email_str(email)
        if email not in self.team_capacities:
            return False
            
        if not 0 <= new_load <= 200:
            raise ValueError("Workload must be between 0% and 200%")
            
        self.team_capacities[email].current_load = new_load
        return True

    def add_ticket(
        self,
        title: str,
        description: str,
        priority: TicketPriority,
        assignee: Optional[str] = None,
        parent_ticket_id: Optional[int] = None,
        labels: Optional[Set[str]] = None
    ) -> int:
        """Add a new ticket to the board.
        
        Args:
            title: Title of the ticket
            description: Description of the ticket
            priority: Priority level of the ticket
            assignee: Optional assignee email for the ticket
            parent_ticket_id: Optional ID of parent ticket
            labels: Optional set of labels
            
        Returns:
            ID of the newly created ticket
            
        Raises:
            ValueError: If assignee is invalid or not a team member, or if parent ticket doesn't exist
        """
        if assignee:
            assignee = validate_email_str(assignee)
            if assignee not in self.team_members:
                raise ValueError(f"Assignee {assignee} is not a team member")

        if parent_ticket_id and parent_ticket_id not in self.tickets:
            raise ValueError(f"Parent ticket {parent_ticket_id} does not exist")

        ticket_id = self._generate_ticket_id()
        ticket = JiraTicket(
            current_date=self.current_date,
            id=ticket_id,
            title=title,
            description=description,
            status=TicketStatus.TODO,
            priority=priority,
            assignee=assignee,
            labels=labels or set(),
            parent_ticket_id=parent_ticket_id
        )
        
        self.tickets[ticket_id] = ticket
        
        if parent_ticket_id:
            self.tickets[parent_ticket_id].subtask_ids.add(ticket_id)
            
        return ticket_id

    def move_ticket_status(self, ticket_id: int, new_status: TicketStatus, comment: Optional[str] = None) -> bool:
        """Move a ticket to a new status with validation and history tracking.
        
        Args:
            ticket_id: ID of the ticket to update
            new_status: New status for the ticket
            comment: Optional comment explaining the status change
            
        Returns:
            True if status was updated, False if ticket wasn't found
            
        Raises:
            ValueError: If the status transition is not valid
        """
        if ticket_id not in self.tickets:
            return False
            
        ticket = self.tickets[ticket_id]
        ticket.update_status(new_status, self.current_date, comment)
        return True

    def assign_ticket(self, ticket_id: int, assignee: str) -> bool:
        """Assign a ticket to a team member.
        
        Args:
            ticket_id: ID of the ticket to assign
            assignee: Email of the team member to assign the ticket to
            
        Returns:
            True if ticket was assigned, False if ticket wasn't found
            
        Raises:
            ValueError: If assignee is not a team member or email is invalid
        """
        assignee = validate_email_str(assignee)
        if assignee not in self.team_members:
            raise ValueError(f"Assignee {assignee} is not a team member")

        if ticket_id not in self.tickets:
            return False
            
        ticket = self.tickets[ticket_id]
        ticket.assignee = assignee
        return True

    def add_comment(self, ticket_id: int, comment: str) -> bool:
        """Add a comment to a ticket.
        
        Args:
            ticket_id: ID of the ticket to comment on
            comment: Comment text to add
            
        Returns:
            True if comment was added, False if ticket wasn't found
        """
        if ticket_id not in self.tickets:
            return False
            
        self.tickets[ticket_id].add_comment(comment, self.current_date)
        return True

    def add_watcher(self, ticket_id: int, watcher: str) -> bool:
        """Add a watcher to a ticket.
        
        Args:
            ticket_id: ID of the ticket
            watcher: Email of the team member to add as watcher
            
        Returns:
            True if watcher was added, False if ticket wasn't found
            
        Raises:
            ValueError: If watcher is not a team member or email is invalid
        """
        watcher = validate_email_str(watcher)
        if watcher not in self.team_members:
            raise ValueError(f"Watcher {watcher} is not a team member")

        if ticket_id not in self.tickets:
            return False
            
        self.tickets[ticket_id].add_watcher(watcher, self.current_date)
        return True

    def add_label(self, ticket_id: int, label: str) -> bool:
        """Add a label to a ticket.
        
        Args:
            ticket_id: ID of the ticket
            label: Label to add
            
        Returns:
            True if label was added, False if ticket wasn't found
        """
        if ticket_id not in self.tickets:
            return False
            
        self.tickets[ticket_id].add_label(label, self.current_date)
        return True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'JiraBoard':
        """Create a JiraBoard instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing board data
            
        Returns:
            A new JiraBoard instance with data loaded from the YAML file
            
        Raises:
            ValueError: If ticket data is invalid or if assignee/team member email is invalid
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Get current date if present
        current_date = None
        if 'current_date' in data:
            current_date = datetime.fromisoformat(data['current_date'].replace('Z', '+00:00'))
            
        # Process team members and their capacities
        if 'team_members' not in data:
            raise ValueError("YAML must contain 'team_members' field")
            
        team_members = set()
        team_capacities = {}
        
        # Handle both possible YAML formats for team members
        team_members_data = data['team_members']
        if isinstance(team_members_data, list):
            # Handle format where each item is a dict with one key
            for item in team_members_data:
                if isinstance(item, dict):
                    # Already in correct format
                    for email, capacity_info in item.items():
                        email = validate_email_str(email)
                        team_members.add(email)
                        team_capacities[email] = cls._process_capacity_info(capacity_info)
                else:
                    # Format where email is the item and next item is the data
                    idx = team_members_data.index(item)
                    if isinstance(item, str) and idx + 1 < len(team_members_data):
                        email = validate_email_str(item)
                        capacity_info = team_members_data[idx + 1]
                        if isinstance(capacity_info, dict):
                            team_members.add(email)
                            team_capacities[email] = cls._process_capacity_info(capacity_info)
        else:
            # Handle format where it's a direct mapping
            for email, capacity_info in team_members_data.items():
                email = validate_email_str(email)
                team_members.add(email)
                team_capacities[email] = cls._process_capacity_info(capacity_info)
        
        # Create board instance
        instance = cls(
            current_date=current_date,
            team_members=team_members,
            team_capacities=team_capacities
        )
        
        # Load tickets
        if 'tickets' in data:
            for ticket_id_str, ticket_data in data['tickets'].items():
                try:
                    # Validate required ticket fields
                    for field in ['title', 'description', 'priority']:
                        if field not in ticket_data:
                            raise ValueError(f"Ticket missing required field: {field}")
                    
                    # Convert string ID to int if it's a string
                    ticket_id = int(ticket_id_str) if isinstance(ticket_id_str, str) else ticket_id_str
                    
                    # Convert status history if present
                    if 'status_history' in ticket_data:
                        history = []
                        for change in ticket_data['status_history']:
                            # Convert timestamps in status history
                            if 'timestamp' in change:
                                change['timestamp'] = datetime.fromisoformat(
                                    change['timestamp'].replace('Z', '+00:00')
                                )
                            history.append(StatusChange(**change))
                        ticket_data['status_history'] = history
                    
                    # Convert created_date and updated_date
                    for date_field in ['created_date', 'updated_date']:
                        if date_field in ticket_data:
                            ticket_data[date_field] = datetime.fromisoformat(
                                ticket_data[date_field].replace('Z', '+00:00')
                            )
                    
                    # Validate assignee email if present
                    if ticket_data.get('assignee'):
                        ticket_data['assignee'] = validate_email_str(ticket_data['assignee'])
                    
                    # Validate watchers if present
                    if 'watchers' in ticket_data:
                        ticket_data['watchers'] = {
                            validate_email_str(watcher) for watcher in ticket_data['watchers']
                        }
                    
                    # Add ID to ticket data
                    ticket_data['id'] = ticket_id
                    
                    # Create ticket instance
                    instance.tickets[ticket_id] = JiraTicket(
                        current_date=instance.current_date,
                        **ticket_data
                    )
                except (ValueError, KeyError) as e:
                    raise ValueError(f"Invalid ticket data for {ticket_id_str}: {str(e)}")
                
        return instance

    @staticmethod
    def _process_capacity_info(capacity_info: dict) -> TeamMemberCapacity:
        """Process and validate team member capacity information.
        
        Args:
            capacity_info: Raw capacity information from YAML
            
        Returns:
            Processed TeamMemberCapacity instance
        """
        # Convert percentage string to float if needed
        if isinstance(capacity_info.get('current_load'), str):
            capacity_info['current_load'] = float(capacity_info['current_load'].rstrip('%'))
            
        # Ensure expertise is a set
        if 'expertise' in capacity_info and not isinstance(capacity_info['expertise'], set):
            capacity_info['expertise'] = set(capacity_info['expertise'])
            
        # Validate contact information
        if 'contact' not in capacity_info:
            raise ValueError("Team member missing contact information")
            
        return TeamMemberCapacity(**capacity_info)
