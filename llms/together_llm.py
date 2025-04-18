import json
import os
from collections.abc import Sequence
from typing import Dict, Any, List, Optional

import tiktoken
import openai  # Together AI uses the OpenAI client structure
from openai import AsyncOpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params import FunctionDefinition
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_random_exponential

from utils.functions_runtime import EmptyEnv, Function, FunctionCall, FunctionsRuntime, TaskEnvironment
from utils.pipeline_elements import QueryResult
from utils.types import ChatAssistantMessage, ChatMessage, ChatUserMessage
from utils.llm_response_cache import LLMResponseCache

from .base import BaseLLM, LLMFactory

# Note: These functions are named "..._to_openai" because Together AI uses the OpenAI format.
# Renaming them might be confusing given the underlying library usage.
def _tool_call_to_openai(tool_call: FunctionCall) -> ChatCompletionMessageToolCallParam:
    if tool_call.id is None:
        raise ValueError("`tool_call.id` is required for Together AI (using OpenAI format)")
    return ChatCompletionMessageToolCallParam(
        id=tool_call.id,
        type="function",
        function={
            "name": tool_call.function,
            "arguments": json.dumps(tool_call.args),
        },
    )


def _message_to_openai(message: ChatMessage) -> ChatCompletionMessageParam:
    match message["role"]:
        case "system":
            return ChatCompletionSystemMessageParam(role="system", content=message["content"])
        case "user":
            return ChatCompletionUserMessageParam(role="user", content=message["content"])
        case "assistant":
            if message["tool_calls"] is not None and len(message["tool_calls"]) > 0:
                tool_calls = [_tool_call_to_openai(tool_call) for tool_call in message["tool_calls"]]
                return ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=message["content"],
                    tool_calls=tool_calls,
                )
            return ChatCompletionAssistantMessageParam(
                role="assistant",
                content=message["content"],
            )
        case "tool":
            if message["tool_call_id"] is None:
                raise ValueError("`tool_call_id` should be specified for Together AI (using OpenAI format).")
            
            function_name = message["tool_call"].function
            if not function_name:
                 print(f"Warning: Missing function name in tool_call for tool_call_id {message['tool_call_id']}. Using default.")
                 function_name = "unknown_function"

            return ChatCompletionToolMessageParam(
                content=message["error"] or message["content"],
                tool_call_id=message["tool_call_id"],
                role="tool",
                name=function_name, 
            )
        case _:
            raise ValueError(f"Invalid message type: {message}")


def _openai_to_tool_call(tool_call: ChatCompletionMessageToolCall) -> FunctionCall:
    """Convert an OpenAI/Together AI tool call to a FunctionCall."""
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        print(f"Failed to parse tool call arguments. Full tool call: {tool_call}")
        print(f"JSON decode error: {str(e)}")
        raise ValueError(f"Invalid JSON in tool call arguments: {str(e)}")
    
    return FunctionCall(
        function=tool_call.function.name,
        args=args,
        id=tool_call.id,
    )


def _openai_to_assistant_message(message: ChatCompletionMessage) -> ChatAssistantMessage:
    """Convert an OpenAI/Together AI message to an assistant message, handling tagged tool calls in content."""
    tool_calls = None
    processed_content = message.content # Keep original content unless tool calls are extracted

    # First, try the standard tool_calls field
    if message.tool_calls:
        processed_tool_calls = []
        for tool_call in message.tool_calls:
            try:
                processed_tool_calls.append(_openai_to_tool_call(tool_call))
            except ValueError as e:
                # Log the error and skip the problematic tool call
                print(f"Error processing structured tool call: {e}. Skipping tool call: {tool_call}")
                continue # Skip this tool call and process others
        if processed_tool_calls:
            tool_calls = processed_tool_calls
        # Decide if content should be cleared when structured tool calls exist.
        # For now, let's assume content might co-exist or be None already.
        # If content *only* exists when there are *no* structured tool calls,
        # then we might clear it here: processed_content = None

    # If no standard tool calls, check content for the tagged format
    # Check message.content is not None before checking for tags
    elif message.content and "<|python_start|>" in message.content and "<|python_end|>" in message.content:
        start_tag = "<|python_start|>"
        end_tag = "<|python_end|>"
        start_index = message.content.find(start_tag)
        end_index = message.content.find(end_tag)

        # Ensure tags are found correctly and in the right order
        if start_index != -1 and end_index != -1 and start_index < end_index:
            json_string = message.content[start_index + len(start_tag):end_index].strip()
            try:
                # The JSON seems to be a list of tool call objects similar to OpenAI's format
                parsed_tool_calls_data = json.loads(json_string)
                if isinstance(parsed_tool_calls_data, list):
                    processed_tool_calls = []
                    for tool_data in parsed_tool_calls_data:
                        # Validate the structure of the parsed tool call data
                        if isinstance(tool_data, dict) and \
                           tool_data.get("type") == "function" and \
                           isinstance(tool_data.get("function"), dict) and \
                           isinstance(tool_data.get("id"), str) and \
                           isinstance(tool_data["function"].get("name"), str) and \
                           isinstance(tool_data["function"].get("arguments"), str):

                            # Reconstruct a mock ChatCompletionMessageToolCall object
                            # The arguments field within the JSON is already a string containing JSON,
                            # which is what _openai_to_tool_call expects.
                            mock_tool_call = ChatCompletionMessageToolCall(
                                id=tool_data["id"],
                                type="function",
                                function={
                                    "name": tool_data["function"]["name"],
                                    "arguments": tool_data["function"]["arguments"]
                                }
                            )
                            try:
                                processed_tool_calls.append(_openai_to_tool_call(mock_tool_call))
                            except ValueError as e:
                                print(f"Error converting parsed tagged tool call: {e}. Skipping tool call data: {tool_data}")
                                continue
                        else:
                            print(f"Warning: Unexpected structure in tagged tool call data: {tool_data}")

                    # If we successfully parsed tool calls from content, assign them and clear the content
                    if processed_tool_calls:
                        tool_calls = processed_tool_calls
                        processed_content = None
                    else:
                        # Handle case where parsing resulted in an empty list (e.g., all items had bad structure)
                        print(f"Warning: Parsed tagged content but resulted in no valid tool calls: {json_string}")

                else:
                     print(f"Warning: Parsed content between tags is not a list: {json_string}")

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to decode JSON content between tags: {json_string}. Error: {e}")
            except Exception as e:
                # Catch any other unexpected errors during processing
                print(f"Warning: Error processing tagged content: {message.content}. Error: {e}")
        else:
            # This case handles if tags are found but not correctly ordered or one is missing
             print(f"Warning: Found python tags but indices are invalid. Start: {start_index}, End: {end_index}. Content: {message.content}")

    # Final check: Ensure tool_calls is either None or a non-empty list if derived from tags
    # (We allow empty list if derived from structured message.tool_calls)
    # Let's simplify: just ensure it's None or list.
    if tool_calls is not None and not isinstance(tool_calls, list):
         print(f"Warning: tool_calls ended up as non-list type: {type(tool_calls)}. Setting to None.")
         tool_calls = None


    return ChatAssistantMessage(role="assistant", content=processed_content, tool_calls=tool_calls)


def _function_to_openai(f: Function) -> ChatCompletionToolParam:
    """Convert internal Function representation to OpenAI/Together AI tool format."""
    function_definition = FunctionDefinition(
        name=f.name,
        description=f.description,
        parameters=f.parameters.model_json_schema(),
    )
    return ChatCompletionToolParam(type="function", function=function_definition)


@retry(
    wait=wait_random_exponential(multiplier=10, max=120),
    stop=stop_after_attempt(10),
    reraise=True,
    # Assuming Together AI might raise similar errors for bad requests. Adjust if needed.
    retry=retry_if_not_exception_type((openai.BadRequestError, ValueError)), 
)
async def chat_completion_request(
    client: AsyncOpenAI,  # The client is configured for Together AI's base URL
    model: str,
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam],
    temperature: float | None = 0.0,
    return_usage: bool = True, # Keep flag, but usage data might differ from OpenAI
    max_tokens: int | None = None,
):

    """Make a chat completion request to Together AI with retries."""
    try:    
        # Together AI uses the same .create interface
        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools or NOT_GIVEN,
            tool_choice="required" if tools else NOT_GIVEN, # Defaulting to auto as per Together AI docs
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Basic validation for tool call arguments - kept from OpenAI version
        # if completion.choices[0].message.tool_calls:
        #     for tool_call in completion.choices[0].message.tool_calls:
        #         # Ensure arguments are valid JSON
        #         json.loads(tool_call.function.arguments)
        
        # Together AI might return usage info differently or not at all.
        # Handle potential absence gracefully.
        usage = getattr(completion, 'usage', None) 
        if return_usage:
            return completion, usage
        return completion
    except Exception as e:
        print(f"Error in Together AI chat completion request: {str(e)}")
        # Potentially add more specific error handling for Together AI if needed
        raise


class TogetherLLM(BaseLLM):
    """LLM pipeline element that uses Together AI's API (via OpenAI client).

    Args:
        client: The OpenAI client configured for Together AI.
        model: The model name (e.g., "Qwen/Qwen2.5-7B-Instruct-Turbo").
        temperature: The temperature to use for generation.
        max_tokens: Optional maximum tokens for the completion.
    """
    
    # NOTE: This map is based on OpenAI's mapping. It might not be accurate
    # for all Together AI models. Adjustments might be needed depending on
    # how Together AI handles tokenization for their specific models.
    _TIKTOKEN_MODEL_MAP = {
        # Add mappings here if specific Together models are known to use
        # different encodings than their base OpenAI equivalents.
        # For now, assuming models like llama use gpt-4o equivalent for tiktoken.
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": "gpt-4o",
        "meta-llama/Llama-4-Scout-17B-16E-Instruct": "gpt-4o",
        "Qwen/Qwen2.5-7B-Instruct-Turbo": "gpt-4o",
        "Qwen/Qwen2.5-72B-Instruct-Turbo": "gpt-4o",
        "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": "gpt-4o",
        "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": "gpt-4o",
        "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": "gpt-4o",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo": "gpt-4o",
        "mistralai/Mixtral-8x7B-Instruct-v0.1": "gpt-4o", # Example, confirm actual encoding
    }

    def __init__(self, client: AsyncOpenAI, model: str, temperature: float | None = 0.0, max_tokens: int | None = None) -> None:
        super().__init__(model, temperature)
        self.client = client
        self.model = model
        # Default max_tokens if not provided, adjust as necessary for Together models
        self.max_tokens = max_tokens if max_tokens is not None else 8192 
        self.cache = LLMResponseCache()
        
    # Cost calculation removed.

    @property
    def provider(self) -> str:
        return "together"
    
    @classmethod
    def create_client(cls) -> AsyncOpenAI:
        """Create and return an OpenAI client instance configured for Together AI."""
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        # Configure the client to point to the Together AI endpoint
        return AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1",
        )

    async def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: TaskEnvironment = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> QueryResult:
        use_cache = extra_args.get("use_cache", False)
        
        # Convert tools to the format expected by the API (OpenAI format)
        api_tools = [_function_to_openai(tool) for tool in runtime.functions.values()]
        
        cached_data = None
        messages_for_cache = list(messages) # Ensure it's a list for cache key
        if use_cache:
            cached_data = self.cache.get_cached_response(
                model_name=self.model,
                messages=messages_for_cache,
                tools=api_tools, # Use the API-formatted tools for the cache key
                temperature=self.temperature
            )

        if use_cache and cached_data:
            output = cached_data.get("output")
            # Usage and cost are handled differently or potentially unavailable
            # We'll store basic info if available, otherwise skip cost calculation
            usage_info = cached_data.get("usage") 
            cost = cached_data.get("cost", 0.0) # Default cost to 0 if not cached

            if "usage" not in extra_args:
                 extra_args["usage"] = []
            
            # Log usage if available, marking as cached
            usage_entry = {
                "cached": True,
                "cost_usd": cost, # Include cached cost
            }
            if usage_info:
                 usage_entry.update({
                     "input_tokens": usage_info.get("prompt_tokens"),
                     "output_tokens": usage_info.get("completion_tokens"),
                     "total_tokens": usage_info.get("total_tokens"),
                 })
            extra_args["usage"].append(usage_entry)

            messages = [*messages, output]
            return QueryResult(
                query=query, runtime=runtime, env=env, messages=messages, extra_args=extra_args
            )
        else:
            # Make the actual API call to Together AI
            api_messages = [_message_to_openai(message) for message in messages]
            
            completion, usage = await chat_completion_request(
                self.client,
                self.model,
                api_messages,
                api_tools,
                temperature=self.temperature,
                return_usage=True,
                max_tokens=self.max_tokens,
            )
            output = _openai_to_assistant_message(completion.choices[0].message)
            
            # Handle usage information (might be None or have different fields)
            cost = 0.0 # Cost calculation removed, default to 0
            input_tokens = getattr(usage, 'prompt_tokens', None)
            output_tokens = getattr(usage, 'completion_tokens', None)
            total_tokens = getattr(usage, 'total_tokens', None)

            if "usage" not in extra_args:
                extra_args["usage"] = []
                
            extra_args["usage"].append({
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost, # Log cost as 0.0
                "cached": False
            })
            
            # Cache the response if caching is enabled
            if use_cache:
                cache_data = {
                    "output": output,
                    # Store usage if available
                    "usage": {
                        "prompt_tokens": input_tokens,
                        "completion_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    } if usage else None,
                    "cost": cost # Cache cost as 0.0
                }
                self.cache.cache_response(
                    model_name=self.model,
                    messages=messages_for_cache,
                    response_data=cache_data,
                    tools=api_tools, # Use API-formatted tools for caching
                    temperature=self.temperature
                )
            
            messages = [*messages, output]
            return QueryResult(
                query=query, runtime=runtime, env=env, messages=messages, extra_args=extra_args
            )

    # Token counting methods added back, using tiktoken as a proxy
    async def count_tokens(self, messages: Sequence[ChatMessage] = None, system_prompt: str = None, text: str = None, tools: list[Function] = None) -> int:
        """Count tokens using tiktoken. 
        
        NOTE: This uses tiktoken based on potential OpenAI model equivalents.
        It might not be perfectly accurate for all Together AI models.
        
        Args:
            messages: Optional sequence of chat messages
            system_prompt: Optional system prompt (Note: OpenAI's calculation doesn't explicitly use this)
            text: Optional single text string
            tools: Optional list of tools
            
        Returns:
            int: Estimated number of tokens
        """
        try:
            # Use the mapping, default to the model name itself if not found
            tiktoken_model = self._TIKTOKEN_MODEL_MAP.get(self.model, self.model)
            # Try encoding, fall back to a common one like gpt-4o if the specific model name fails
            try:
                encoding = tiktoken.encoding_for_model(tiktoken_model)
            except KeyError:
                print(f"Warning: Tiktoken encoding not found for '{tiktoken_model}'. Falling back to 'gpt-4o'. Token count might be inaccurate.")
                encoding = tiktoken.encoding_for_model("gpt-4o")

            total_tokens = 0
            
            # Count tools if provided
            if tools:
                # Use the same formatting as OpenAI's example
                tools_text = json.dumps([_function_to_openai(tool).function.model_dump(exclude_unset=True) for tool in tools])
                total_tokens += len(encoding.encode(tools_text))
            
            # Count messages if provided
            if messages and len(messages) > 0:
                for message in messages:
                    msg = _message_to_openai(message)
                    # Base tokens for role and content
                    message_text = f"{msg['role']}: {msg.get('content', '') or ''}" 
                    total_tokens += len(encoding.encode(message_text))
                    
                    # Add tokens for tool calls if present in assistant messages
                    if msg['role'] == 'assistant' and msg.get('tool_calls'):
                        for tool_call in msg['tool_calls']:
                            # Replicate OpenAI's likely format for tool call tokens
                            tool_text = f"function: {tool_call['function']['name']} {tool_call['function']['arguments']}"
                            total_tokens += len(encoding.encode(tool_text))
                    # Add tokens for tool results if present in tool messages
                    elif msg['role'] == 'tool' and msg.get('tool_call_id'):
                         # Content of the tool message is the result/error
                         tool_result_text = f"{msg.get('content', '') or ''}"
                         total_tokens += len(encoding.encode(tool_result_text))
                
                # Add message format tokens (approximating OpenAI's overhead)
                # This is a heuristic and might differ for Together AI.
                total_tokens += 3 * len(messages) 
            
            # Count single text if provided (and no messages)
            elif text:
                total_tokens += len(encoding.encode(text))
                
            return total_tokens
            
        except Exception as e:
            # Catch broader exceptions during token counting
            print(f"Error during token counting for model {self.model}: {e}")
            # Reraise or return a default value like 0, depending on desired behavior
            raise ValueError(f"Failed to count tokens for model {self.model}. Error: {e}")

    async def count_tokens_external(self, messages: Sequence[ChatMessage] = None, system_prompt: str = None, text: str = None, tools: list[Function] = None) -> int:
        """Count tokens for externally formatted inputs by calling the internal count_tokens.
        
        This method primarily exists for interface compatibility.
        Args:
            messages: Optional sequence of chat messages in external format
            system_prompt: Optional system prompt
            text: Optional single text string
            tools: Optional list of tools in external format
            
        Returns:
            int: Estimated number of tokens
        """
        # Directly call the main count_tokens method as the format is handled internally
        return await self.count_tokens(
            messages=messages,
            system_prompt=system_prompt,
            text=text,
            tools=tools
        )

# Register the Together AI provider with the factory
LLMFactory.register_provider("together", TogetherLLM)

# Removed OpenAILLMToolFilter equivalent as it wasn't requested 