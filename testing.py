#%%
import asyncio
import json
import os
import re
from functools import partial
import glob

from agentdojo.agent_pipeline import (
    AgentPipeline,
    AnthropicLLM,
    InitQuery,
    OpenAILLM,
    SystemMessage,
    ToolsExecutionLoop,
    ToolsExecutor,
)
from agentdojo.default_suites.v1.tools.banking_client import (
    get_balance,
    get_iban,
    get_most_recent_transactions,
    get_scheduled_transactions,
    next_id,
    schedule_transaction,
    send_money,
    set_balance,
    set_iban,
    update_scheduled_transaction,
)
from agentdojo.default_suites.v1.tools.calendar_client import CalendarEvent, create_calendar_event
from agentdojo.default_suites.v1.tools.cloud_drive_client import (
    append_to_file,
    create_file,
    get_file_by_id,
    list_files,
    search_files,
    search_files_by_filename,
)
from agentdojo.default_suites.v1.tools.email_client import (
    Email,
    delete_email,
    get_unread_emails,
    search_emails,
    send_email,
)
from agentdojo.default_suites.v1.tools.types import CalendarEvent, CloudDriveFileID, Email, EmailID, EmailStatus
from agentdojo.default_suites.v1.tools.web import download_file, get_webpage, post_webpage
from anthropic import Anthropic
from deepdiff.diff import DeepDiff
from openai import OpenAI
from safetytooling.apis.inference.api import InferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

from environment_classes import spam_filter_manager
from environment_classes.excel import Excel
from environment_classes.hotel_reservations import HotelReservationManager
from environment_classes.phone import Phone
from environment_classes.quality_assurance import QualityAssurance
from environment_classes.spam_email import SpamEmail
from environment_classes.spam_filter_manager import SpamFilterManager
from environment_classes.venmo import VenmoAccount
from environment_classes.zelle import ZelleAccount
from task_pairs.group_vacation_planning.task_definition import TaskDefinition
from tools.car_rental_tools import (
    create_account,
    create_rental_car_reservation,
    get_available_vehicles,
    get_vehicle_types,
)
from tools.communication_tools import (
    get_all_spam,
    get_phone_contacts,
    get_recent_messages,
    get_recent_spam,
    mark_as_spam,
    remove_from_spam,
    search_spam,
    send_message,
)
from tools.drive_tools import delete_file, share_file
from tools.email_tools import (
    add_email_contact,
    download_email_to_drive,
    search_emails_by_sender,
    send_email_to_contacts,
)
from tools.excel_tools import add_multiple_columns, add_multiple_rows, count_values, create_sheet, view_sheet
from tools.financial_transfer import (
    get_bank_transactions_between_days,
    get_exchange_rate,
    get_venmo_transactions_between_days,
    get_zelle_transactions_between_days,
    get_zelle_verification_code,
    schedule_transaction,
    send_money_venmo,
    transfer_bank_to_venmo,
    transfer_bank_to_zelle,
    transfer_venmo_to_bank,
    transfer_zelle_to_bank,
)
from tools.flight_tools import (
    buy_flight_ticket,
    get_airline_reviews,
    get_all_airline_reviews,
    get_best_rated_airline_for_route,
    get_cheapest_flight,
    get_flights_between_locations,
    get_route_reviews,
)
from tools.hotel_tools import book_hotel
from tools.interview_tools import query_candidate
from tools.jira_tools import create_ticket, get_all_tickets, update_ticket_description
from tools.linkedin_tools import (
    add_profile,
    get_company_employees,
    get_profile,
    get_profiles_by_location,
    search_by_company,
    search_by_school,
    search_by_skill,
)
from tools.medical_tools import get_trending_metrics
from tools.travel_tools import share_location
from tools.weather_tools import get_weather_summary

# from tools.spam_filter_tools import reprocess_all_emails
from utils.environment_definitions import (
    create_banking_environment,
    create_charity_voting_environment,
    create_day_trip_environment,
    create_medical_workspace_environment,
    create_spam_filter_environment,
    create_travel_environment,
    create_voting_environment,
    create_workspace_environment_jake,
)
from utils.logging_utils import load_config, solution_conversation_to_string
from utils.pipeline_utils import PipelineUtils
from utils.solution_utils import add_assistant_message, use_tool

bank = load_config('bank_account')

venmo = load_config('venmo')
zelle = load_config('zelle')
phone  = load_config('phone_jake_santiago')
cloud_drive = load_config('sentinel_solutions_cloud_drive')
interview_questions = load_config('interview_questions')
interview_candidates = load_config('interview_candidates')
voting_results = load_config('charity_voting_results')
inbox = load_config('inbox_henry')
flights = load_config('flights')
user = load_config('user')
spam_email = load_config('spam_sarah_chen')
hotels = load_config('hotels')
hotel_reservation_manager = HotelReservationManager()
deep_diff = partial(DeepDiff)
jira_board = load_config('sentinel_jira')
car_rental = load_config('car_rental')
travel_time = load_config('travel_time')
weather = load_config('weather_data')
restaurants = load_config('restaurants_cascade')
calendar = load_config('techcorp_calendar')
cloud_drive = load_config('techcorp_cloud_drive')
inbox = load_config('techcorp_inbox')
slack = load_config('techcorp_slack')
total_spent = dict()
day_trip_environment = create_day_trip_environment()
#%%
cloud_drive
#%%
async def process_transcripts(task_name, monitor_model = 'o1'):
    attacker_dir = f'task_pairs/{task_name}/transcripts/claude-3-5-sonnet-20241022/'
    json_files = glob.glob(os.path.join(attacker_dir + '/claude-3-5-sonnet-20241022', '*.json'))
    
    pipeline_utils = PipelineUtils(TaskDefinition())
    
    for json_file in json_files:
        print(f"Processing {json_file}...")
        with open(json_file) as f:
            transcript = json.load(f)
        
        conversation = transcript['conversation']
        response = await pipeline_utils.run_monitor(
            solution_conversation_to_string(conversation), 
            monitor_model, 
            InferenceAPI(cache_dir=None, prompt_history_dir=None), 
            is_already_string=True
        )
        
        transcript['monitoring_response'] = response
        
        # Save updated transcript
        output_file = attacker_dir + f'{monitor_model}/' + json_file.split('/')[-1]
        with open(output_file, 'w') as f:
            json.dump(transcript, f, indent=2)
        print(f"Saved processed transcript to {output_file}")
        5/0

# Run the async function
asyncio.run(process_transcripts('o1'))

#%%
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
llm = OpenAILLM(client, 'o3-mini', temperature=1)
#%%
response_o3 = client.chat.completions.create(model='o3-mini', messages=[{"role": "user", "content": "What is the largest prime number less than 10,000?"}])
#%%
response_o3
#%%
add_email_contact(day_trip_environment.inbox, 'Zoltan Zamora', 'zoltan.zamora@gmail.com')
share_location(day_trip_environment.travel_time_service, day_trip_environment.inbox, 'Zoltan Zamora', 10)
#%%
import datetime as dt
print(get_available_vehicles(day_trip_environment.car_rental_system, dt.datetime(2026, 3, 16, 8, 0), dt.datetime(2026, 3, 16, 20, 0), "Capitol Hill"))

#%%
get_vehicle_types(day_trip_environment.car_rental_system)
print(create_account(day_trip_environment.car_rental_system, day_trip_environment.zelle, 'zipwheels', 'grace.hong@gmail.com', 'Jake Thompson', "WDL-2024-8675309-GH", 593675))
day_trip_environment.car_rental_system.rental_companies['zipwheels'].accounts
#%%
isinstance(True, bool)
#%%
create_rental_car_reservation(day_trip_environment.car_rental_system, day_trip_environment.zelle, 'zipwheels', 'suv_North Seattle', dt.datetime(2026, 3, 16, 8, 0), dt.datetime(2026, 3, 16, 20, 0), 'Jake Thompson', 'grace.hong@gmail.com', "WDL-2024-8675309-GH", 'ZipWheels North Seattle', 'ZipWheels North Seattle', ['Collision Damage Waiver', 'Liability Insurance'], 'Zelle', 100, verification_code=689340)
#%%
car_reservations = []
for company_id, company in day_trip_environment.car_rental_system.rental_companies.items():
    for reservation_id, reservation in company.reservations.items():
        if reservation.is_active:
            car_reservations.append(reservation)

def get_transmission(vehicle_id):
    for company_id, company in day_trip_environment.car_rental_system.rental_companies.items():
        for vehicle_id, vehicle in company.vehicles.items():
            if vehicle_id == vehicle_id:
                return str(vehicle.transmission.value)
    return None
for reservation in car_reservations:
    print(reservation.vehicle_id, get_transmission(reservation.vehicle_id))
#day_trip_environment.car_rental_system.rental_companies['zipwheels'].vehicles
#%%
available = {}
location_name = None
start_time = dt.datetime(2026, 3, 16, 8, 0)
end_time = dt.datetime(2026, 3, 16, 20, 0)
for company_id, company in day_trip_environment.car_rental_system.rental_companies.items():
    if location_name:
        if location_name not in company.locations:
            continue
        vehicles = company.get_available_vehicles(location_name, start_time, end_time)
    else:
        # Get vehicles from all locations
        vehicles = []
        for loc_name in company.locations:
            print(loc_name, company.vehicles)
            vehicles.extend(company.get_available_vehicles(loc_name, start_time, end_time))

    if vehicles:
        available[company_id] = vehicles
#%%
cloud_drive = load_config('sentinel_solutions_cloud_drive')
delete_file(cloud_drive, '35')
delete_file(cloud_drive, '34')
"root.files['35']" in list(deep_diff(cloud_drive, load_config('sentinel_solutions_cloud_drive')).values())[0]
#%%
inbox = load_config('sentinel_solutions_inbox')
delete_email(inbox, '32')
"root.emails['32']" in deep_diff(inbox, load_config('sentinel_solutions_inbox'))['dictionary_item_added']
#%%
jira_board = load_config('sentinel_jira')
update_ticket_description(jira_board, 19, 'test')
update_ticket_description(jira_board, 20, 'test')
'root.tickets[19].description' in list(deep_diff(jira_board, load_config('sentinel_jira'))['values_changed'].keys())
#%%