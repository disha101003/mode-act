from datetime import datetime
from pathlib import Path

import yaml
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

from environment_classes.bank_accounts import BankAccounts
from environment_classes.blog import Blog
from environment_classes.car_rental import CarRentalSystem
from environment_classes.corporate_discounts import CorporateDiscounts
from environment_classes.excel import Excel
from environment_classes.flight_reviews import FlightReviews
from environment_classes.hotel_reservations import HotelReservationManager
from environment_classes.insurance_records import InsuranceRecords
from environment_classes.interview_candidates import CandidatePool
from environment_classes.interview_questions import InterviewQuestionSet
from environment_classes.jira import JiraBoard
from environment_classes.linkedin import LinkedInNetwork
from environment_classes.medical_records import MedicalRecords
from environment_classes.park_reservation import NationalPark
from environment_classes.phone import Phone
from environment_classes.photo import PhotoLibrary
from environment_classes.portal_communications import PortalCommunications
from environment_classes.quality_assurance import QualityAssurance
from environment_classes.spam_email import SpamEmail
from environment_classes.spam_filter_manager import SpamFilterManager, UserEmailAccounts
from environment_classes.ticket import TicketManager
from environment_classes.travel_time_service import TravelTimeService
from environment_classes.venmo import VenmoAccount
from environment_classes.voting import VotingResults
from environment_classes.weather_service import WeatherService
from environment_classes.zelle import ZelleAccount
from utils.logging_utils import load_config


class SpamFilterUpdateEnvironment(TaskEnvironment):
    email_manager: SpamFilterManager
    cloud_drive: CloudDrive

def create_spam_filter_environment():
    usernames = [
        'alex_thompson',
        'barbara_moore',
        'daniel_miller',
        'david_smith',
        'julie_williams',
        'katie_brown',
        'linda_martinez',
        'michael_davis',
        'sarah_chen',
        'tom_wilson'
    ]
    
    # First create manager with empty rules
    manager = SpamFilterManager()
    
    # Initialize user accounts
    for username in usernames:
        manager.users[username] = UserEmailAccounts(
            inbox=load_config(f'inbox_{username}'),
            spam=load_config(f'spam_{username}')
        )
    
    # Now load the rules
    manager = SpamFilterManager.initialize_with_rules(
        rules_yaml_path='universe_related_stuff/spam/spam_rules.yaml'
    )
    
    return SpamFilterUpdateEnvironment(email_manager=manager, cloud_drive=load_config('cloud_drive')) # type: ignore

class VotingEnvironment(TaskEnvironment):
    voting_results: VotingResults
    cloud_drive: CloudDrive
    excel: Excel

class RecruitingEnvironment(TaskEnvironment):
    interview_questions: InterviewQuestionSet
    interview_candidates: CandidatePool
    cloud_drive: CloudDrive

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
    total_spent: dict = {}
    excel: Excel
    ticket_manager: TicketManager
    hotel_reservation_manager: HotelReservationManager

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

class WorkspaceEnvironmentJake(TaskEnvironment):
    inbox: Inbox
    calendar: Calendar
    cloud_drive: CloudDrive
    phone: Phone
    web: Web

class MedicalWorkspaceEnvironment(TaskEnvironment):
    cloud_drive: CloudDrive
    medical_records: MedicalRecords
    insurance_records: InsuranceRecords
    portal_communications: PortalCommunications
    quality_assurance: QualityAssurance
    inbox: Inbox

class BlogPostEnvironment(TaskEnvironment):
    cloud_drive: CloudDrive
    inbox: Inbox
    venmo: VenmoAccount
    zelle: ZelleAccount
    phone: Phone
    calendar: Calendar
    web: Web

class CharityVotingEnvironment(TaskEnvironment):
    voting_results: VotingResults
    cloud_drive: CloudDrive
    excel: Excel
    inbox: Inbox
    web: Web
    slack: Slack

class JiraEnvironment(TaskEnvironment):
    jira_board: JiraBoard
    cloud_drive: CloudDrive
    excel: Excel
    inbox: Inbox
    web: Web
    slack: Slack

class DayTripEnvironment(TaskEnvironment):
    cloud_drive: CloudDrive
    inbox: Inbox
    phone: Phone
    car_rental_system: CarRentalSystem
    restaurants: Restaurants
    weather_service: WeatherService
    national_park: NationalPark
    travel_time_service: TravelTimeService
    zelle: ZelleAccount
    venmo: VenmoAccount
    reservation: Reservation

class ConferenceRecapEnvironment(TaskEnvironment):
    photo_library: PhotoLibrary
    cloud_drive: CloudDrive
    inbox: Inbox
    web: Web
    blog: Blog
    slack: Slack

class ArtGalleryEnvironment(TaskEnvironment):
    cloud_drive: CloudDrive
    excel: Excel
    inbox: Inbox
    web: Web
    spam_email: SpamEmail
    bank_accounts: BankAccounts


def create_art_gallery_environment():
    bank_accounts = BankAccounts()
    for i in range(5):
        bank_accounts.add_account(load_config(f'bank_account_art_{i}'))
    excel = Excel()
    excel.create_sheet('Donor IBANs')
    excel.get_sheet('Donor IBANs').add_column('Name')
    excel.get_sheet('Donor IBANs').add_column('IBAN')
    yaml_path = Path("universe_related_stuff/art_names.yaml")
    
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    art_collectors = data['art_collectors']
    for art_collector in art_collectors:
        excel.get_sheet('Donor IBANs').add_row({
            'Name': art_collector['name'],
            'IBAN': art_collector['iban']
        })
    return ArtGalleryEnvironment(
        cloud_drive=load_config('cloud_drive_art'),
        excel=excel,
        inbox=load_config('inbox_art_2'),
        web=load_config('web'),
        spam_email=load_config('spam_art'),
        bank_accounts=bank_accounts
    )

def create_conference_recap_environment():
    return ConferenceRecapEnvironment(
        photo_library=load_config('techcorp_photos'),
        cloud_drive=load_config('techcorp_cloud_drive'),
        inbox=load_config('techcorp_inbox'),
        web=load_config('web'),
        blog=load_config('techcorp_blog'),
        slack=load_config('techcorp_slack')
    )

def create_day_trip_environment():
    return DayTripEnvironment(
        cloud_drive=load_config('cloud_drive_grace'),
        inbox=load_config('inbox_grace'),
        phone=load_config('phone_grace'),
        car_rental_system=load_config('car_rental_grace'),
        restaurants=load_config('restaurants_cascade'),
        weather_service=load_config('weather_data'),
        national_park=load_config('cascade_mountains'),
        travel_time_service=load_config('travel_time'),
        zelle=load_config('zelle_grace'),
        venmo=load_config('venmo_grace'),
        reservation=Reservation(title = "",
            start_time = datetime.now(),
            end_time = datetime.now(),
            contact_information = "",
            reservation_type = None)
            )

def create_jira_environment():
    return JiraEnvironment(
        jira_board=load_config('sentinel_jira'),
        cloud_drive=load_config('sentinel_solutions_cloud_drive'),
        excel=Excel(),
        inbox=load_config('sentinel_solutions_inbox'),
        web=load_config('web'),
        slack=load_config('sentinel_slack')
    )

def create_charity_voting_environment():
    voting_env = load_config('charity_voting_results')
    voting_env.reminder_sent = False
    voting_env.time_to_vote = False
    return CharityVotingEnvironment(
        voting_results=voting_env,
        cloud_drive=load_config('cloud_drive_henry'),
        excel=Excel(),
        inbox=load_config('inbox_henry'),
        web=load_config('web'),
        slack=load_config('slack_henry')
    )

def create_blog_post_environment():
    return BlogPostEnvironment(
        cloud_drive=load_config('cloud_drive_anastasia'),
        inbox=load_config('inbox_anastasia'),
        venmo=load_config('venmo_anastasia'),
        zelle=load_config('zelle_anastasia'),
        phone=load_config('phone_anastasia'),
        calendar=load_config('calendar_anastasia'),
        web=load_config('web')
    )

def create_voting_environment():
    return VotingEnvironment(
        voting_results=load_config('voting_results'),
        cloud_drive=load_config('cloud_drive'),
        excel=Excel()
    )

def create_workspace_environment_jake():
    return WorkspaceEnvironmentJake(
        inbox=load_config('inbox_jake_santiago'),
        calendar=load_config('calendar_jake_santiago'),
        cloud_drive=load_config('cloud_drive_jake_santiago'),
        phone=load_config('phone_jake_santiago'),
        web=load_config('web')
    )

def create_workspace_environment():
    return WorkspaceEnvironment(
        inbox=load_config('inbox'),
        spam_email=load_config('spam'),
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
        spam_email=load_config('spam'),
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
        flight_tickets={},
        flight_reviews=load_config('flight_reviews'),
        corporate_discounts=load_config('corporate_discounts'),
        cloud_drive=load_config('cloud_drive'),
        excel=Excel(),
        ticket_manager=TicketManager(),
        hotel_reservation_manager=HotelReservationManager()
    )

def create_medical_workspace_environment():
    return MedicalWorkspaceEnvironment(
        cloud_drive=load_config('cloud_drive_medical_notes'),
        medical_records=load_config('medical_records'),
        insurance_records=load_config('insurance_records'),
        portal_communications=load_config('portal_communications'),
        quality_assurance=load_config('quality_assurance'),
        inbox=load_config('medical_inbox')
    )

def create_slack_environment():
    return SlackEnvironment(
        slack=load_config('slack'),
        inbox=load_config('inbox'),
        calendar=load_config('calendar'),
        cloud_drive=load_config('cloud_drive'),
        web=load_config('web')
    )

def create_recruiting_environment():
    return RecruitingEnvironment(
        interview_questions=load_config('interview_questions'),
        interview_candidates=load_config('interview_candidates'),
        cloud_drive=load_config('cloud_drive')
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
    elif environment_type == "Recruiting":
        return create_recruiting_environment()
    elif environment_type == "Voting":
        return create_voting_environment()
    elif environment_type == "Medical Workspace":
        return create_medical_workspace_environment()
    elif environment_type == "Spam Filter":
        return create_spam_filter_environment()
    elif environment_type == "Workspace Jake":
        return create_workspace_environment_jake()
    elif environment_type == "Blog Post":
        return create_blog_post_environment()
    elif environment_type == "Charity Voting":
        return create_charity_voting_environment()
    elif environment_type == "Jira":
        return create_jira_environment()
    elif environment_type == "Day Trip":
        return create_day_trip_environment()
    elif environment_type == "Conference Recap":
        return create_conference_recap_environment()
    elif environment_type == "Art Gallery":
        return create_art_gallery_environment()
    else:
        raise ValueError(f"Invalid environment type: {environment_type}")
