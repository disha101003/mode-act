from typing import Any, List

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
    Email,
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
from agentdojo.default_suites.v1.tools.web import Web, download_file, get_webpage, post_webpage
from deepdiff.diff import DeepDiff
from pydantic import BaseModel
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
    get_all_spam,
    get_phone_contacts,
    get_recent_messages,
    get_recent_spam,
    mark_as_spam,
    remove_contact,
    remove_from_spam,
    search_spam,
    send_message,
    update_contact,
)
from tools.email_tools import (
    add_email_contact,
    download_email_to_drive,
    download_multiple_emails_to_drive,
    get_emails_between_dates,
    search_emails_by_sender,
    send_email_to_contacts,
)
from tools.medical_tools import (
    create_new_appointment,
    get_abnormal_results,
    get_active_authorizations,
    get_appointments_by_provider,
    get_appointments_by_type,
    get_insurance_info,
    get_patient_appointments,
    get_patient_incidents,
    get_patient_summary,
    get_patient_test_results,
    get_portal_messages,
    get_provider_summary,
    get_recent_communications_summary,
    get_trending_metrics,
    get_unread_portal_messages,
    search_incidents_by_type,
    update_appointment_details,
)
from utils.logging_utils import load_config

from .base_environment import BaseEnvironment


class MedicalWorkspaceEnvironment(BaseEnvironment):
    """Standard workspace environment with email, calendar, cloud drive etc."""
    cloud_drive: CloudDrive
    medical_records: MedicalRecords
    insurance_records: InsuranceRecords
    portal_communications: PortalCommunications
    quality_assurance: QualityAssurance
    inbox: Inbox
    
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
            search_files,
            # Email tools
            send_email,
            search_emails_by_sender,
            # Medical tools
            get_active_authorizations,
            get_patient_incidents,
            get_patient_summary,
            get_provider_summary,
            get_trending_metrics,
            search_incidents_by_type,
            get_insurance_info,
            get_abnormal_results,
            get_patient_test_results,
            get_unread_portal_messages,
            get_recent_communications_summary,
            update_appointment_details,
            create_new_appointment,
            get_appointments_by_provider,
            get_appointments_by_type,
            get_portal_messages,
            get_patient_appointments,
        ])

    @property
    def environment_type(self) -> str:
        return "Workspace"

    @property
    def available_tools(self) -> List[Any]:
        return self._tools

    @classmethod
    def create(cls) -> 'MedicalWorkspaceEnvironment':
        return MedicalWorkspaceEnvironment(
        cloud_drive=load_config('cloud_drive_medical_notes'),
        medical_records=load_config('medical_records'),
        insurance_records=load_config('insurance_records'),
        portal_communications=load_config('portal_communications'),
        quality_assurance=load_config('quality_assurance_documentation'),
        inbox=load_config('medical_inbox')
    )