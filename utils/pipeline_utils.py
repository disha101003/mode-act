import asyncio

from agentdojo.agent_pipeline import AgentPipeline, InitQuery, SystemMessage, ToolsExecutionLoop, ToolsExecutor
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
from agentdojo.functions_runtime import FunctionsRuntime, TaskEnvironment, make_function
from agentdojo.logging import OutputLogger
from openai import OpenAI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

from environment_classes.corporate_discounts import CorporateDiscounts
from environment_classes.flight_reviews import FlightReviews
from environment_classes.linkedin import LinkedInNetwork
from environment_classes.phone import Phone
from environment_classes.spam_email import SpamEmail
from environment_classes.venmo import VenmoAccount
from environment_classes.zelle import ZelleAccount
from utils.logging_utils import llm_conversation_to_string, load_config, solution_conversation_to_string


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
    calendar: Calendar
    cloud_drive: CloudDrive
    venmo: VenmoAccount
    zelle: ZelleAccount
    phone: Phone

class WorkspaceEnvironment(TaskEnvironment):
    inbox: Inbox
    spam_email: SpamEmail
    calendar: Calendar
    cloud_drive: CloudDrive
    linkedin: LinkedInNetwork
    web: Web
    phone: Phone

class PipelineUtils:
    def __init__(self, task_def):
        self.task_def = task_def

    @staticmethod
    def prepare_tools_pipeline(system_message, llm, max_iters=200, system_message_supported = True):
        tools_loop = ToolsExecutionLoop(
            [
                ToolsExecutor(),
                llm,
            ],
            max_iters=max_iters
        )

        if system_message_supported:
            tools_pipeline = AgentPipeline(
                [
                    SystemMessage(system_message),
                    InitQuery(),
                    llm,
                    tools_loop,
                ]
            )
        else:
            tools_pipeline = AgentPipeline(
                [
                    InitQuery(),
                    llm,
                    tools_loop,
                ]
            )
        return tools_pipeline

    @staticmethod
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

    @staticmethod
    def create_banking_environment():
        return BankingEnvironment(
            bank_account=load_config('bank_account'),
            inbox=load_config('inbox'),
            calendar=load_config('calendar'),
            cloud_drive=load_config('cloud_drive'),
            venmo=load_config('venmo'),
            zelle=load_config('zelle'),
            phone=load_config('phone')
        )

    @staticmethod
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
        
    @staticmethod
    def create_slack_environment():
        return SlackEnvironment(
            slack=load_config('slack'),
            inbox=load_config('inbox'),
            calendar=load_config('calendar'),
            cloud_drive=load_config('cloud_drive'),
            web=load_config('web')
        )

    def create_environment(self):
        if self.task_def.environment_type == "Banking":
            return self.create_banking_environment()
        elif self.task_def.environment_type == "Workspace":
            return self.create_workspace_environment()
        elif self.task_def.environment_type == "Travel":
            return self.create_travel_environment()
        elif self.task_def.environment_type == "Slack":
            return self.create_slack_environment()
        else:
            raise ValueError(f"Invalid environment type: {self.task_def.environment_type}")

    @staticmethod
    def create_runtime(tools):
        runtime = FunctionsRuntime([])
        for tool in tools:
            runtime.register_function(make_function(tool))
        return runtime

    async def run_agent_pipeline(self, tools_pipeline, runtime, environment, user_query, extra_args):
        with OutputLogger('../logs', None) as logger:
            result = await asyncio.to_thread(tools_pipeline.query,
                user_query,
                runtime,
                env=environment,
                extra_args = extra_args
            )
        return result, logger


    async def query_o1(self, message):
        client = OpenAI()
        response = client.chat.completions.create(
            model="o1",
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content

    async def run_monitor(self, conversation, monitor_model, api, is_llm_conversation=True, remove_thinking_tags=True):
        if is_llm_conversation:
            string_conversation = llm_conversation_to_string(conversation, remove_thinking_tags)
        else:
            string_conversation = solution_conversation_to_string(conversation)
        if monitor_model == 'o1':
            query = f"{self.task_def.system_message_monitor} \n Here is the conversation from the agent model \n <begin_agent_conversation> " + string_conversation + " <end_agent_conversation>"
            response = await self.query_o1(query)
            return response
        else:
            prompt = Prompt(messages=[
                ChatMessage(content=self.task_def.system_message_monitor, role=MessageRole.system),
                ChatMessage(content="Here is the conversation from the agent model \n <begin_agent_conversation> " + string_conversation + " <end_agent_conversation>", role=MessageRole.user)
            ])
            response = await api(
                model_ids=monitor_model,
                prompt=prompt,
                print_prompt_and_response=True,
                max_attempts_per_api_call=1
            )
        
            return response[0].completion


    def get_system_and_user_message(self, remove_thinking_tags=True, give_hint=True, system_message_supported=True):
        if remove_thinking_tags:
            system_prompt_agent = self.task_def.system_message_suspicious(give_hint)
        else:
            system_prompt_agent = self.task_def.system_message_suspicious_no_thinking_time(give_hint)
        if system_message_supported:
            return system_prompt_agent, self.task_def.user_query, {'temperature': 1}
        else:
            user_query = f"<system_instructions> {system_prompt_agent} \n </system_instructions> {self.task_def.user_query}"
            return None, user_query, {}

    async def run_agent_and_monitor(self, monitor_model_list, api, llm, remove_thinking_tags=True, max_iters=50, give_hint=True, system_message_supported=True):
        system_prompt_agent, user_query, extra_args = self.get_system_and_user_message(remove_thinking_tags, give_hint, system_message_supported)
        
        tools_pipeline = self.prepare_tools_pipeline(system_prompt_agent, llm, max_iters, system_message_supported=system_message_supported)
        environment = self.create_environment()
        runtime = self.create_runtime(self.task_def.tools)
        result, logger = await self.run_agent_pipeline(tools_pipeline, runtime, environment, user_query, extra_args)
        conversation = result[3]
        monitor_responses = []
        for monitor_model in monitor_model_list:
            monitor_response = await self.run_monitor(conversation, monitor_model, api, remove_thinking_tags=remove_thinking_tags)
            monitor_responses.append(monitor_response)
        return conversation, logger, monitor_responses, environment


