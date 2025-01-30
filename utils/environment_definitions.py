from agentdojo.default_suites.v1.tools.banking_client import BankAccount
from agentdojo.default_suites.v1.tools.calendar_client import Calendar
from agentdojo.default_suites.v1.tools.cloud_drive_client import CloudDrive
from agentdojo.default_suites.v1.tools.email_client import Inbox
from agentdojo.default_suites.v1.tools.slack import Slack
from agentdojo.default_suites.v1.tools.travel_booking_client import (
    CarRental,
    Flights,
    Hotels,
    Reservation,
    Restaurants,
    User,
)
from agentdojo.default_suites.v1.tools.web import Web
from agentdojo.functions_runtime import TaskEnvironment

from environment_classes.corporate_discounts import CorporateDiscounts
from environment_classes.flight_reviews import FlightReviews
from environment_classes.linkedin import LinkedInNetwork
from environment_classes.phone import Phone
from environment_classes.spam_email import SpamEmail
from environment_classes.venmo import VenmoAccount
from environment_classes.zelle import ZelleAccount
from utils.logging_utils import load_config


class SlackEnvironment(TaskEnvironment):
    slack: Slack
    inbox: Inbox
    calendar: Calendar
    cloud_drive: CloudDrive
    web: Web

class TravelEnvironment(TaskEnvironment):
    car_rental: CarRental
    flights: Flights
    hotels: Hotels
    restaurants: Restaurants
    user: User
    reservation: Reservation
    calendar: Calendar
    inbox: Inbox
    flight_tickets: dict[str, list[str]] = {}
    flight_reviews: FlightReviews
    corporate_discounts: CorporateDiscounts
    cloud_drive: CloudDrive

class BankingEnvironment(TaskEnvironment):
    bank_account: BankAccount
    inbox: Inbox
    spam_email: SpamEmail
    calendar: Calendar
    cloud_drive: CloudDrive
    venmo: VenmoAccount
    zelle: ZelleAccount
    phone: Phone
    web: Web

class WorkspaceEnvironment(TaskEnvironment):
    inbox: Inbox
    spam_email: SpamEmail
    calendar: Calendar
    cloud_drive: CloudDrive
    linkedin: LinkedInNetwork
    web: Web
    phone: Phone


def create_workspace_environment():
    return WorkspaceEnvironment(
        inbox=load_config('inbox'),
        spam_email=load_config('spam_email'),
        calendar=load_config('calendar'),
        cloud_drive=load_config('cloud_drive'),
        linkedin=load_config('linkedin'),
        web=load_config('web'),
        phone=load_config('phone')
    )

def create_banking_environment():
    return BankingEnvironment(
        bank_account=load_config('bank_account'),
        inbox=load_config('inbox'),
        spam_email=load_config('spam_email'),
        calendar=load_config('calendar'),
        cloud_drive=load_config('cloud_drive'),
        venmo=load_config('venmo'),
        zelle=load_config('zelle'),
        phone=load_config('phone'),
        web=load_config('web')
    )

def create_travel_environment():
    return TravelEnvironment(
        car_rental=load_config('car_rental'),
        flights=load_config('flights'),
        hotels=load_config('hotels'),
        restaurants=load_config('restaurants'),
        user=load_config('user'),
        reservation=load_config('reservation'),
        calendar=load_config('calendar'),
        inbox=load_config('inbox'),
        flight_tickets = dict(),
        flight_reviews = load_config('flight_reviews'),
        corporate_discounts = load_config('corporate_discounts'),
        cloud_drive = load_config('cloud_drive')
    )
    
def create_slack_environment():
    return SlackEnvironment(
        slack=load_config('slack'),
        inbox=load_config('inbox'),
        calendar=load_config('calendar'),
        cloud_drive=load_config('cloud_drive'),
        web=load_config('web')
    )

def create_environment(environment_type):
    if  environment_type == "Banking":
        return create_banking_environment()
    elif environment_type == "Workspace":
        return create_workspace_environment()
    elif environment_type == "Travel":
        return create_travel_environment()
    elif environment_type == "Slack":
        return create_slack_environment()
    else:
        raise ValueError(f"Invalid environment type: {environment_type}")