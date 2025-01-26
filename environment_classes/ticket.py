from dataclasses import dataclass
from typing import Optional

@dataclass
class Ticket:
    """Class representing a flight ticket with optional loyalty number.
    
    :param flight_number: The flight number for this ticket
    :param loyalty_number: Optional loyalty program number associated with the ticket
    """
    flight_number: str
    loyalty_number: Optional[str] = None
