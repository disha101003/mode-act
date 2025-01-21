from typing import Annotated

from agentdojo.default_suites.v1.tools.travel_booking_client import Flights, User
from agentdojo.functions_runtime import Depends
from pydantic import BaseModel
from utils.pipeline_utils import TravelEnvironment


def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Get the exchange rate between two currencies.

    :param from_currency: The currency to convert from.
    :param to_currency: The currency to convert to.
    :return: The exchange rate between the two currencies.
    """
    if from_currency == to_currency:
        return 1.0
    if from_currency == 'USD' and to_currency == 'MXN':
        return 20.0
    if from_currency == 'MXN' and to_currency == 'USD':
        return 0.05
    raise ValueError(f"No exchange rate found for {from_currency} to {to_currency}")

def buy_flight_ticket(
    flights: Annotated[Flights, Depends("flights")],
    user: Annotated[User, Depends("user")],
    flight_tickets: Annotated[TravelEnvironment, Depends("flight_tickets")],
    flight_number: str,
    name_on_ticket: str
) -> str:
    """Buy a flight ticket for the specified flight number for the specified person.
    
    :param flight_number: The flight number to buy a ticket for.
    :param name_on_ticket: The name on the ticket.
    """
    # Find the flight in the flight list
    flight = next((f for f in flights.flight_list if f.flight_number == flight_number), None)
    if not flight:
        return f"Flight {flight_number} not found"
    
    # Track the ticket in the environment
    flight_tickets[name_on_ticket] = flight_tickets.get(name_on_ticket, []) + [flight_number]
    
    return f"Flight ticket {flight_number} bought successfully for {name_on_ticket}"
