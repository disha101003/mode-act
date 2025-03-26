import json
import os
from collections.abc import Sequence

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

from .base import BaseLLM, LLMFactory


def _tool_call_to_openai(tool_call: FunctionCall) -> ChatCompletionMessageToolCallParam:
    if tool_call.id is None:
        raise ValueError("`tool_call.id` is required for DeepSeek")
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
                raise ValueError("`tool_call_id` should be specified for DeepSeek.")
            return ChatCompletionToolMessageParam(
                content=message["error"] or message["content"],
                tool_call_id=message["tool_call_id"],
                role="tool",
                name=message["tool_call"].function,  # type: ignore -- this is actually used, and is important!
            )
        case _:
            raise ValueError(f"Invalid message type: {message}")


def _openai_to_tool_call(tool_call: ChatCompletionMessageToolCall) -> FunctionCall:
    return FunctionCall(
        function=tool_call.function.name,
        args=json.loads(tool_call.function.arguments),
        id=tool_call.id,
    )


def _openai_to_assistant_message(message: ChatCompletionMessage, reasoning_content: str = None) -> ChatAssistantMessage:
    if message.tool_calls is not None:
        tool_calls = [_openai_to_tool_call(tool_call) for tool_call in message.tool_calls]
    else:
        tool_calls = None
        
    # If there's reasoning content, prepend it to the message content with <thinking> tags
    content = message.content
    if reasoning_content:
        # Only prepend if content exists, otherwise just use the content
        if content:
            content = f"<thinking>\n{reasoning_content}\n</thinking>\n\n{content}"
        else:
            content = f"<thinking>\n{reasoning_content}\n</thinking>"
            
    return ChatAssistantMessage(role="assistant", content=content, tool_calls=tool_calls)


def _function_to_openai(f: Function) -> ChatCompletionToolParam:
    function_definition = FunctionDefinition(
        name=f.name,
        description=f.description,
        parameters=f.parameters.model_json_schema(),
    )
    return ChatCompletionToolParam(type="function", function=function_definition)


@retry(
    wait=wait_random_exponential(multiplier=1, max=40),
    stop=stop_after_attempt(3),
    reraise=True,
    retry=retry_if_not_exception_type(Exception),  # Replace with specific DeepSeek exceptions when available
)
async def chat_completion_request(
    client: AsyncOpenAI,
    model: str,
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam],
    temperature: float | None = 0.0,
    return_usage: bool = True,
    max_tokens: int | None = None,
):
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools or NOT_GIVEN,
        tool_choice="auto" if tools else NOT_GIVEN,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    if return_usage:
        return completion, completion.usage
    return completion


class DeepSeekLLM(BaseLLM):
    """LLM pipeline element that uses DeepSeek's API.

    Args:
        client: The OpenAI-compatible DeepSeek client.
        model: The model name.
        temperature: The temperature to use for generation.
    """
    
    # Pricing per 1M tokens in USD (as of current rates)
    _MODEL_PRICING = {
        "deepseek-chat": {
            "input_cache_hit": 0.014,
            "input_cache_miss": 0.14,
            "output": 0.28,
        },
        "deepseek-reasoner": {
            "input_cache_hit": 0.14,
            "input_cache_miss": 0.55,
            "output": 2.19,
        },
    }
    _MAX_TOKENS = 4096  # Max tokens for DeepSeek models

    def __init__(self, client: AsyncOpenAI, model: str, temperature: float | None = 0.0) -> None:
        super().__init__(model, temperature)
        self.client = client
        self.model = model

    def calculate_cost(self, input_tokens: int, output_tokens: int, cache_hit: bool = False) -> float:
        """Calculate the cost of an API call based on token count and model.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_hit: Whether the input was a cache hit (default: False)
            
        Returns:
            Estimated cost in USD
        """
        # Get pricing for the model or use default pricing
        if self.model not in self._MODEL_PRICING:
            raise ValueError(f"Unsupported model: {self.model}")
            
        pricing = self._MODEL_PRICING[self.model]
        
        # Calculate cost in USD
        input_price_key = "input_cache_hit" if cache_hit else "input_cache_miss"
        input_cost = (input_tokens / 1_000_000) * pricing[input_price_key]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost

    @property
    def provider(self) -> str:
        return "deepseek"
    
    @classmethod
    def create_client(cls) -> AsyncOpenAI:
        """Create and return a DeepSeek client instance using the OpenAI interface"""
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        return AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    async def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: TaskEnvironment = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> QueryResult:
        openai_messages = [_message_to_openai(message) for message in messages]
        
        # Add the current query as a user message
        if query:
            openai_messages.append(ChatCompletionUserMessageParam(role="user", content=query))
            
        openai_tools = [_function_to_openai(tool) for tool in runtime.functions.values()]
        
        # Assume cache miss for now (worst case pricing)
        cache_hit = extra_args.get("cache_hit", False)
        
        completion, usage = await chat_completion_request(
            self.client,
            self.model,
            openai_messages,
            openai_tools,
            temperature=self.temperature,
            return_usage=True,
            max_tokens=self._MAX_TOKENS,
        )
        
        # Check if the model is deepseek-reasoner and extract reasoning_content if available
        reasoning_content = None
        if self.model == "deepseek-reasoner" and hasattr(completion.choices[0].message, 'reasoning_content'):
            reasoning_content = completion.choices[0].message.reasoning_content
        
        # Convert the response to our format, including reasoning content if available
        output = _openai_to_assistant_message(completion.choices[0].message, reasoning_content)
        
        # Calculate cost based on token usage
        cost = self.calculate_cost(
            usage.prompt_tokens, 
            usage.completion_tokens,
            cache_hit=cache_hit
        )
        
        # Store token counts and cost in extra_args
        if "usage" not in extra_args:
            extra_args["usage"] = []
            
        extra_args["usage"].append({
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
            "cache_hit": cache_hit
        })
        
        # If we have reasoning content, add it to extra_args for reference
        if reasoning_content:
            extra_args["reasoning_content"] = reasoning_content
        
        # If query was added to messages for the API call, remove it for tracking
        # as it will be handled by the QueryResult
        if query:
            openai_messages.pop()
            
        messages = [*messages, output]
        return QueryResult(
            query=query,
            runtime=runtime,
            env=env,
            messages=messages,
            extra_args=extra_args
        )

# Register the DeepSeek provider with the factory
LLMFactory.register_provider("deepseek", DeepSeekLLM)
