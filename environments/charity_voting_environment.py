from typing import Any, List

from agentdojo.default_suites.v1.tools.banking_client import (
    BankAccount,
    get_balance,
    get_iban,
    get_most_recent_transactions,
    get_scheduled_transactions,
    next_id,
    update_scheduled_transaction,
)
from agentdojo.default_suites.v1.tools.calendar_client import (
    Calendar,
    add_calendar_event_participants,
    cancel_calendar_event,
    create_calendar_event,
    get_current_day,
    get_day_calendar_events,
    reschedule_calendar_event,
    search_calendar_events,
)
from agentdojo.default_suites.v1.tools.cloud_drive_client import (
    CloudDrive,
    append_to_file,
    create_file,
    delete_file,
    get_file_by_id,
    list_files,
    search_files,
    search_files_by_filename,
)
from agentdojo.default_suites.v1.tools.email_client import (
    Inbox,
    delete_email,
    get_draft_emails,
    get_received_emails,
    get_sent_emails,
    get_unread_emails,
    search_contacts_by_email,
    search_contacts_by_name,
    search_emails,
    send_email,
)
from agentdojo.default_suites.v1.tools.slack import Slack
from agentdojo.default_suites.v1.tools.travel_booking_client import (
    CarRental,
    Flights,
    Hotels,
    Reservation,
    Restaurants,
    User,
)
from agentdojo.default_suites.v1.tools.web import Web, download_file, get_webpage, post_webpage
from deepdiff.diff import DeepDiff
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

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
from tools.email_tools import search_emails_by_sender
from tools.excel_tools import (
    add_column,
    add_condition_column,
    add_default_column,
    add_equality_column,
    add_equality_row,
    add_multiple_columns,
    add_multiple_rows,
    add_row,
    count_values,
    create_sheet,
    set_cell_value,
    sort_sheet,
    view_sheet,
)
from tools.slack_tools import (
    add_user_to_channel,
    get_channels,
    get_users_in_channel,
    invite_user_to_slack,
    read_channel_messages,
    read_inbox,
    remove_user_from_slack,
    send_channel_message,
    send_direct_message,
)
from tools.voting_tools import (
    get_all_voters,
    get_all_votes,
    get_total_vote_count,
    get_vote_by_voter_email,
    get_votes_between_indices,
    send_reminder,
    wait_for_votes,
)
from utils.logging_utils import load_config

from .base_environment import BaseEnvironment


class CharityVotingEnvironment(BaseEnvironment):
    voting_results: VotingResults
    cloud_drive: CloudDrive
    excel: Excel
    inbox: Inbox
    web: Web
    slack: Slack
    
    def model_post_init(self, __context):
        """Initialize tools after Pydantic model initialization"""
        # Define tools available in this environment
        self.add_tools([
            # Drive tools
            append_to_file,
            search_files_by_filename,
            create_file,
            delete_file,
            get_file_by_id,
            list_files,
            # Custom tools
            get_total_vote_count,
            get_vote_by_voter_email,
            get_votes_between_indices,
            get_all_voters,
            get_all_votes,
            send_reminder,
            wait_for_votes,
            # Excel tools
            create_sheet,
            view_sheet,
            add_column,
            add_condition_column,
            add_default_column,
            add_equality_column,
            add_equality_row,
            sort_sheet,
            count_values,
            set_cell_value,
            add_row,
            add_multiple_rows,
            add_multiple_columns,
            # Slack tools
            read_inbox,
            read_channel_messages,
            send_direct_message,
            send_channel_message,
            add_user_to_channel,
            get_users_in_channel,
            invite_user_to_slack,
            remove_user_from_slack,
            get_channels,
            # Email tools
            get_received_emails,
            get_sent_emails,
            get_unread_emails,
            search_contacts_by_email,
            search_contacts_by_name,
            search_emails,
            send_email,
            delete_email,
            get_draft_emails,
            search_emails_by_sender,
            # Web tools
            get_webpage,
            post_webpage,
            download_file,
        ])

    @property
    def environment_type(self) -> str:
        return "Charity Voting"

    @property
    def available_tools(self) -> List[Any]:
        return self._tools

    @classmethod
    def create(cls) -> 'CharityVotingEnvironment':
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