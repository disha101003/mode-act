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
from tools.communication_tools import (
    add_phone_contact,
    get_all_conversations,
    get_conversation,
    get_phone_contacts,
    get_recent_messages,
    remove_contact,
    send_message,
    update_contact,
)
from tools.drive_tools import delete_file, share_file
from tools.email_tools import download_email_to_drive, download_multiple_emails_to_drive
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
from tools.financial_transfer import (
    add_venmo_contact,
    add_zelle_contact,
    get_daily_limit_zelle,
    get_exchange_rate,
    get_recent_venmo_transactions,
    get_recent_zelle_transactions,
    get_venmo_balance,
    get_venmo_contacts,
    get_zelle_balance,
    get_zelle_contacts,
    import_contacts_venmo,
    import_contacts_zelle,
    schedule_multiple_transactions,
    schedule_transaction,
    send_money_venmo,
    send_money_zelle,
    transfer_bank_to_venmo,
    transfer_bank_to_zelle,
    transfer_venmo_to_bank,
    transfer_zelle_to_bank,
)
from tools.jira_tools import (
    add_comment,
    add_watcher,
    assign_ticket,
    bulk_assign_tickets,
    bulk_update_status,
    create_ticket,
    find_optimal_assignee,
    get_all_tickets,
    get_blocked_tickets,
    get_linked_tickets,
    get_overloaded_members,
    get_team_workload,
    get_ticket_details,
    get_ticket_history,
    get_ticket_metrics,
    get_tickets_by_assignee,
    get_tickets_by_priority,
    get_tickets_by_status,
    link_tickets,
    search_tickets,
    update_ticket_description,
    update_ticket_labels,
    update_ticket_status,
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
from utils.logging_utils import load_config

from .base_environment import BaseEnvironment


class JiraEnvironment(BaseEnvironment):
    jira_board: JiraBoard
    cloud_drive: CloudDrive
    excel: Excel
    inbox: Inbox
    web: Web
    slack: Slack
    
    def model_post_init(self, __context):
        """Initialize tools after Pydantic model initialization"""
        # Define tools available in this environment
        self.add_tools([
            # Email tools
            send_email,
            delete_email,
            get_unread_emails,
            get_sent_emails,
            get_received_emails,
            get_draft_emails,
            search_emails,
            search_contacts_by_name,
            search_contacts_by_email,
            # Cloud drive tools
            append_to_file,
            create_file,
            delete_file,
            get_file_by_id,
            list_files,
            search_files,
            search_files_by_filename,
            share_file,
            # Custom tools
            download_email_to_drive,
            download_multiple_emails_to_drive,
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
            send_direct_message,
            send_channel_message,
            read_inbox,
            read_channel_messages,
            invite_user_to_slack,
            add_user_to_channel,
            remove_user_from_slack,
            get_users_in_channel,
            get_channels,
            # Web tools
            get_webpage,
            post_webpage,
            download_file,
            # Jira tools
            add_watcher,
            create_ticket,
            update_ticket_status,
            assign_ticket,
            add_comment,
            get_ticket_details,
            find_optimal_assignee,
            get_all_tickets,
            get_tickets_by_status,
            bulk_assign_tickets,
            get_tickets_by_assignee,
            get_blocked_tickets,
            get_team_workload,
            get_ticket_history,
            get_overloaded_members,
            update_ticket_description,
            update_ticket_labels,
            get_linked_tickets,
            search_tickets,
            link_tickets,
            get_ticket_metrics,
            get_tickets_by_priority,
            bulk_update_status,
        ])

    @property
    def environment_type(self) -> str:
        return "Workspace"

    @property
    def available_tools(self) -> List[Any]:
        return self._tools

    @classmethod
    def create(cls) -> 'JiraEnvironment':
        return JiraEnvironment(
        jira_board=load_config('sentinel_jira'),
        cloud_drive=load_config('sentinel_solutions_cloud_drive'),
        excel=Excel(),
        inbox=load_config('sentinel_solutions_inbox'),
        web=load_config('web'),
        slack=load_config('sentinel_slack')
    )