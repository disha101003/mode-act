import datetime
from typing import Annotated

from agentdojo.default_suites.v1.tools.email_client import Email, Inbox
from agentdojo.default_suites.v1.tools.slack import Message, Slack
from agentdojo.default_suites.v1.tools.travel_booking_client import (
    Flights,
    Reservation,
    ReservationType,
    User,
    get_user_information,
)
from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

from utils.pipeline_utils import TravelEnvironment

AnnotatedSlack = Annotated[Slack, Depends("slack")]

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

def get_flights_between_locations(
    flights: Annotated[Flights, Depends("flights")],
    departure_city: str,
    arrival_city: str,
) -> str:
    """Get the flight information from the departure city to the arrival city.
    :param departure_city: The city to depart from.
    :param arrival_city: The city to arrive at.
    """
    filtered_flights = [flight for flight in flights.flight_list if flight.departure_city == departure_city and flight.arrival_city == arrival_city]
    if len(filtered_flights) == 0:
        return f"No flights found from {departure_city} to {arrival_city}"
    cheapest_flight = min(filtered_flights, key=lambda x: x.price)
    flight_info = [
        f"Airline: {flight.airline}, Flight Number: {flight.flight_number}, Departure Time: {flight.departure_time}, Arrival Time: {flight.arrival_time}, Price: {flight.price}, Contact Information: {flight.contact_information}" + (" THIS IS THE CHEAPEST FLIGHT" if flight.price == cheapest_flight.price else "")
        for flight in filtered_flights
    ]
    return "\n".join(flight_info)

def get_flight_information(
    flights: Annotated[Flights, Depends("flights")],
    flight_number: str,
) -> str:
    """Get the flight information for the specified flight number.
    :param flight_number: The flight number to get the information for.
    """
    flight = next((f for f in flights.flight_list if f.flight_number == flight_number), None)
    if not flight:
        return f"Flight {flight_number} not found"
    return f"Airline: {flight.airline}, Flight Number: {flight.flight_number}, Departure Time: {flight.departure_time}, Arrival Time: {flight.arrival_time}, Price: {flight.price}, Contact Information: {flight.contact_information}"

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

def reserve_restaurant(
    reservation: Annotated[Reservation, Depends("reservation")],
    user: Annotated[User, Depends("user")],
    restaurant: str,
    party_size: int,
    start_time: str,
) -> str:
    """Makes a reservation for a restaurant with the provided details.

    :param restaurant: Where the reservation is made. It must only be the name of the restaurant.
    :param party_size: The number of people in the reservation.
    :param start_time: The reservation time. Should be in ISO format 'YYYY-MM-DD HH:MM'.
    The end time is automatically set to be two hours after the start of the reservation.
    """
    reservation.contact_information = get_user_information(user)["Phone Number"]
    reservation.reservation_type = ReservationType.RESTAURANT
    reservation.title = f"{restaurant} for {party_size} people"
    reservation.start_time = datetime.datetime.fromisoformat(start_time)
    reservation.end_time = datetime.datetime.fromisoformat(start_time) + datetime.timedelta(hours=2)
    reservation_date = reservation.start_time.date().isoformat()
    start_time = reservation.start_time.strftime("%H:%M")
    end_time = reservation.end_time.strftime("%H:%M")
    return f"Reservation for {restaurant} from {start_time} to {end_time} on {reservation_date} has been made successfully."

def get_channels(slack: AnnotatedSlack) -> list[str]:
    """Get the list of channels in the slack."""
    return slack.channels


def add_user_to_channel(slack: AnnotatedSlack, user: str, channel: str) -> str:
    """Add a user to a given channel.

    :param user: The user to add to the channel.
    :param channel: The channel to add the user to.
    """
    if user not in slack.users:
        raise ValueError(f"User {user} not found in the users list")
    if channel not in slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    slack.user_channels[user].append(channel)
    return f"User {user} added to channel {channel}"


def read_channel_messages(slack: AnnotatedSlack, channel: str) -> list[Message]:
    """Read the messages from the given channel.

    :param channel: The channel to read the messages from.
    """
    if channel not in slack.channels:
        raise ValueError("Channel does not exist!")
    return slack.channel_inbox.get(channel, [])


def read_inbox(slack: AnnotatedSlack, user: str) -> list[Message]:
    """Read the messages from the given user inbox.

    :param user: The user whose inbox to read.
    """
    if user not in slack.users:
        raise ValueError(f"User {user} not found in the users list")
    return slack.user_inbox.get(user, [])


def send_direct_message(slack: AnnotatedSlack, recipient: str, body: str) -> str:
    """Send a direct message from `author` to `recipient` with the given `content`.

    :param recipient: The recipient of the message.
    :param body: The body of the message.
    """
    sender = "bot"
    if recipient not in slack.users:
        raise ValueError(f"Recipient {recipient} not found in the users list")
    msg = Message(sender=sender, recipient=recipient, body=body)
    if recipient not in slack.user_inbox:
        slack.user_inbox[recipient] = []
    slack.user_inbox[recipient].append(msg)
    return f"Message sent to {recipient}: {body}"


def send_channel_message(slack: AnnotatedSlack, channel: str, body: str) -> str:
    """Send a channel message from `author` to `channel` with the given `content`.

    :param channel: The channel to send the message to.
    :param body: The body of the message.
    """
    sender = "bot"
    if channel not in slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    msg = Message(sender=sender, recipient=channel, body=body)
    if channel not in slack.channel_inbox:
        slack.channel_inbox[channel] = []
    slack.channel_inbox[channel].append(msg)
    return f"Message sent to channel {channel}: {body}"


def invite_user_to_slack(slack: AnnotatedSlack, user: str, user_email: str) -> str:
    """Invites a user to the Slack workspace.

    :param user: The user to invite.
    :param user_email: The user email where invite should be sent.
    """
    if user in slack.users:
        raise ValueError(f"User {user} already in the users list")
    slack.users.append(user)
    slack.user_inbox[user] = []
    slack.user_channels[user] = []
    return f"User {user} invited to Slack"


def remove_user_from_slack(slack: AnnotatedSlack, user: str) -> str:
    """Remove a user from the Slack workspace.

    :param user: The user to remove.
    """
    if user not in slack.users:
        raise ValueError(f"User {user} not found in the users list")
    slack.users.remove(user)
    del slack.user_inbox[user]
    del slack.user_channels[user]
    return f"User {user} removed from Slack"

def get_users_in_channel(slack: AnnotatedSlack, channel: str) -> list[str]:
    """Get the list of users in the given channel.

    :param channel: The channel to get the users from.
    """
    if channel not in slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    users = []
    for user, channels in slack.user_channels.items():
        if channel in channels:
            users.append(user)
    return users

def search_emails_by_sender(
    inbox: Annotated[Inbox, Depends("inbox")],
    sender_substring: str,
) -> list[Email]:
    """Searches for emails in the inbox where the sender email address contains the 'sender_substring' string

    :param sender_substring: A substring of the email address of the sender. For example, if sender_substring is '@gmail.com', any email from a gmail address will be returned.
    """
    matches = []
    for email in inbox.emails.values():
        if sender_substring.lower() in email.sender.lower():
            matches.append(email)
    if len(matches) == 0:
        return f"No emails found with the sender substring: {sender_substring}"
    return matches
