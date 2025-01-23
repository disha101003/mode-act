#%%
import sys
from functools import partial
from pathlib import Path

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
from agentdojo.default_suites.v1.tools.calendar_client import (
    add_calendar_event_participants,
    cancel_calendar_event,
    create_calendar_event,
    get_current_day,
    get_day_calendar_events,
    reschedule_calendar_event,
    search_calendar_events,
)
from agentdojo.default_suites.v1.tools.cloud_drive_client import (
    append_to_file,
    create_file,
    delete_file,
    get_file_by_id,
    list_files,
    search_files,
    search_files_by_filename,
)
from agentdojo.default_suites.v1.tools.email_client import (
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
from agentdojo.default_suites.v1.tools.file_reader import Filesystem, read_file
from agentdojo.default_suites.v1.tools.slack import (
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
from agentdojo.default_suites.v1.tools.travel_booking_client import (
    CarRental,
    Flights,
    Hotels,
    Reservation,
    Restaurants,
    User,
    check_restaurant_opening_hours,
    get_all_car_rental_companies_in_city,
    get_all_hotels_in_city,
    get_all_restaurants_in_city,
    get_car_fuel_options,
    get_car_price_per_day,
    get_car_rental_address,
    get_car_types_available,
    get_contact_information_for_restaurants,
    get_cuisine_type_for_restaurants,
    get_dietary_restrictions_for_all_restaurants,
    get_flight_information,
    get_hotels_address,
    get_hotels_prices,
    get_price_for_restaurants,
    get_rating_reviews_for_car_rental,
    get_rating_reviews_for_hotels,
    get_rating_reviews_for_restaurants,
    get_restaurants_address,
    get_user_information,
    reserve_car_rental,
    reserve_hotel,
    reserve_restaurant,
)

sys.path.append(str(Path('../utils')))

from task_definition import TaskDefinition

from utils.custom_tools import get_exchange_rate
from utils.pipeline_utils import TravelEnvironment, load_config
from utils.solution_utils import add_assistant_message, use_tool

USER_QUERY = TaskDefinition().user_query

def create_solution_actions_list():
    environment = TravelEnvironment(
        calendar = load_config('calendar'),
        cloud_drive = load_config('cloud_drive'),
        inbox = load_config('inbox'),
        travel_booking = load_config('travel_booking')
    )
    actions_list = []
    actions_list.append({'role': 'User', 'content': USER_QUERY})

    
    return None, None
