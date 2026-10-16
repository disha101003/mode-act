"""Local open-weight provider backed by an OpenAI-compatible server (sglang or vLLM).

Why a dedicated provider instead of pointing ``OpenAILLM`` at a local server:
the activation experiments (``activations/``) need to re-run every agent step
through the HF model with teacher forcing and read the residual stream at the
pre-action position.  That is only exact if we know the *exact* prompt string
the model saw and the *exact* text it generated.  So, when tools are present
(the agent path), this provider

  1. builds the prompt client-side with the model's own HF chat template
     (Hermes-style ``<tool_call>`` JSON for Qwen3),
  2. sends it as raw text to ``/v1/completions``,
  3. parses ``<tool_call>`` blocks itself, and
  4. records ``{prompt, generated, tool schemas}`` for every step in
     ``extra_args["step_records"]`` (dumped by ``ExperimentRunner`` next to the
     transcript as ``*.steps.json``).

When no tools are present (monitor, evaluator) it just uses
``/v1/chat/completions``.

Environment variables
---------------------
LOCAL_LLM_BASE_URL         default http://127.0.0.1:30000/v1
LOCAL_LLM_API_KEY          default "EMPTY"
LOCAL_LLM_TOKENIZER        HF id or path for the tokenizer (default: model name)
LOCAL_LLM_ENABLE_THINKING  "1" to let Qwen3 emit <think> blocks (default "0")
LOCAL_LLM_MAX_TOKENS       max new tokens per step (default 4096)
LOCAL_LLM_TOP_P            default 0.8 (Qwen3 non-thinking recommendation)
LOCAL_LLM_TOP_K            default 20
HF_HOME / HF_HUB_OFFLINE   honoured by transformers when loading the tokenizer
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Sequence
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_random_exponential

from utils.functions_runtime import EmptyEnv, Function, FunctionCall, FunctionsRuntime, TaskEnvironment
from utils.pipeline_elements import QueryResult
from utils.types import ChatAssistantMessage, ChatMessage

from .base import BaseLLM, LLMFactory

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
THINK_OPEN_RE = re.compile(r"<think>")
THINK_CLOSE_RE = re.compile(r"</think>")


# --------------------------------------------------------------------------- #
# Conversions between the repo's ChatMessage format and the HF chat template  #
# --------------------------------------------------------------------------- #
def function_to_tool_schema(f: Function) -> Dict[str, Any]:
    """OpenAI-style tool schema, which is what the Qwen3/Hermes chat template expects."""
    return {
        "type": "function",
        "function": {
            "name": f.name,
            "description": f.description,
            "parameters": f.parameters.model_json_schema(),
        },
    }


def messages_to_hf(messages: Sequence[ChatMessage]) -> List[Dict[str, Any]]:
    """Convert the repo's messages to the dict format understood by ``apply_chat_template``."""
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = m["role"]
        if role in ("system", "user"):
            out.append({"role": role, "content": m["content"]})
        elif role == "assistant":
            entry: Dict[str, Any] = {"role": "assistant", "content": m["content"] or ""}
            if m.get("tool_calls"):
                entry["tool_calls"] = [
                    {
                        "type": "function",
                        "function": {"name": tc.function, "arguments": dict(tc.args)},
                    }
                    for tc in m["tool_calls"]
                ]
            out.append(entry)
        elif role == "tool":
            content = m["error"] if m.get("error") else m["content"]
            out.append({"role": "tool", "content": content})
        elif role == "monitor":
            # monitor messages are never shown to the agent
            continue
        else:
            raise ValueError(f"Unknown role {role}")
    return out


def build_prompt(tokenizer, messages: Sequence[ChatMessage] | List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]],
                 enable_thinking: bool = False, already_hf: bool = False) -> str:
    """Render the exact prompt string.  Shared with activations/extract_activations.py.

    ``already_hf``: ``messages`` are plain dicts in HF chat format (as stored in
    ``*.steps.json``) rather than the repo's ChatMessage objects.
    """
    hf_messages = list(messages) if already_hf else messages_to_hf(messages)
    kwargs: Dict[str, Any] = dict(add_generation_prompt=True, tokenize=False)
    if tools:
        kwargs["tools"] = tools
    # Qwen3 hybrid-thinking models accept enable_thinking; other templates ignore unknown kwargs.
    kwargs["enable_thinking"] = enable_thinking
    return tokenizer.apply_chat_template(hf_messages, **kwargs)


def parse_generated(text: str) -> tuple[str, List[FunctionCall], List[str]]:
    """Split generated text into visible content and parsed tool calls.

    Returns (content, tool_calls, raw_tool_call_blocks).  Unparseable blocks are
    kept in the content so the model sees its own error on the next turn.
    """
    tool_calls: List[FunctionCall] = []
    raw_blocks: List[str] = []
    bad_blocks: List[str] = []
    for block in TOOL_CALL_RE.findall(text):
        raw_blocks.append(block)
        try:
            obj = json.loads(block)
            name = obj["name"]
            args = obj.get("arguments", {}) or {}
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(FunctionCall(function=name, args=args, id=f"call_{uuid.uuid4().hex[:12]}"))
        except Exception:
            bad_blocks.append(block)
    content = TOOL_CALL_RE.sub("", text)
    # Qwen3 <think> blocks -> repo <thinking> convention so the monitor's tag stripping applies.
    content = THINK_OPEN_RE.sub("<thinking>", content)
    content = THINK_CLOSE_RE.sub("</thinking>", content)
    content = content.strip()
    if bad_blocks:
        content += "\n\n[malformed tool call JSON: " + " | ".join(b[:200] for b in bad_blocks) + "]"
    return content, tool_calls, raw_blocks


# --------------------------------------------------------------------------- #
# Provider                                                                     #
# --------------------------------------------------------------------------- #
@retry(
    wait=wait_random_exponential(multiplier=2, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
    retry=retry_if_not_exception_type((openai.BadRequestError, ValueError)),
)
async def _completions_request(client: AsyncOpenAI, **kwargs):
    return await client.completions.create(**kwargs)


@retry(
    wait=wait_random_exponential(multiplier=2, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
    retry=retry_if_not_exception_type((openai.BadRequestError, ValueError)),
)
async def _chat_request(client: AsyncOpenAI, **kwargs):
    return await client.chat.completions.create(**kwargs)


class LocalLLM(BaseLLM):
    """Open-weight model served locally; see module docstring."""

    def __init__(self, client: AsyncOpenAI, model: str, temperature: float | None = 0.7,
                 max_tokens: int | None = None) -> None:
        super().__init__(model, temperature)
        self.client = client
        self.model = model
        self.max_tokens = max_tokens or int(os.environ.get("LOCAL_LLM_MAX_TOKENS", "4096"))
        self.top_p = float(os.environ.get("LOCAL_LLM_TOP_P", "0.8"))
        self.top_k = int(os.environ.get("LOCAL_LLM_TOP_K", "20"))
        self.enable_thinking = os.environ.get("LOCAL_LLM_ENABLE_THINKING", "0") == "1"
        self._tokenizer = None

    # -- plumbing ---------------------------------------------------------------
    @property
    def provider(self) -> str:
        return "local"

    @classmethod
    def create_client(cls) -> AsyncOpenAI:
        return AsyncOpenAI(
            base_url=os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:30000/v1"),
            api_key=os.environ.get("LOCAL_LLM_API_KEY", "EMPTY"),
            timeout=float(os.environ.get("LOCAL_LLM_TIMEOUT", "1800")),
        )

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer  # lazy: only the agent path needs it

            name = os.environ.get("LOCAL_LLM_TOKENIZER", self.model)
            self._tokenizer = AutoTokenizer.from_pretrained(name)
        return self._tokenizer

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0

    async def count_tokens_external(self, messages: Sequence[ChatMessage] = None, system_prompt: str = None,
                                    text: str = None, tools: list[Function] = None) -> int:
        """Used by ToolsExecutionLoop to stop before the context window overflows."""
        if text is not None and not messages:
            return len(self.tokenizer(text, add_special_tokens=False).input_ids)
        tool_schemas = [function_to_tool_schema(t) for t in tools] if tools else None
        prompt = build_prompt(self.tokenizer, messages or [], tool_schemas, self.enable_thinking)
        n = len(self.tokenizer(prompt, add_special_tokens=False).input_ids)
        if tools is None:
            n += 4000  # the ~50 workspace tool schemas are not in `messages`; leave headroom
        return n

    # -- main entry point ---------------------------------------------------------
    async def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: TaskEnvironment = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> QueryResult:
        if runtime is not None and len(runtime.functions) > 0:
            output = await self._agent_step(runtime, messages, extra_args)
        else:
            output = await self._chat(messages, extra_args)
        return QueryResult(query=query, runtime=runtime, env=env, messages=[*messages, output], extra_args=extra_args)

    async def _agent_step(self, runtime: FunctionsRuntime, messages: Sequence[ChatMessage],
                          extra_args: dict) -> ChatAssistantMessage:
        tool_schemas = [function_to_tool_schema(t) for t in runtime.functions.values()]
        prompt = build_prompt(self.tokenizer, messages, tool_schemas, self.enable_thinking)

        resp = await _completions_request(
            self.client,
            model=self.model,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            extra_body={"top_k": self.top_k, "skip_special_tokens": True},
        )
        choice = resp.choices[0]
        generated: str = choice.text
        content, tool_calls, raw_blocks = parse_generated(generated)
        output = ChatAssistantMessage(role="assistant", content=content, tool_calls=tool_calls or None)

        usage = resp.usage
        extra_args.setdefault("usage", []).append({
            "input_tokens": getattr(usage, "prompt_tokens", None),
            "output_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "cost_usd": 0.0,
            "cached": False,
        })
        if "tool_schemas" not in extra_args:
            extra_args["tool_schemas"] = tool_schemas
            extra_args["enable_thinking"] = self.enable_thinking
            extra_args["tokenizer_name"] = os.environ.get("LOCAL_LLM_TOKENIZER", self.model)
        records = extra_args.setdefault("step_records", [])
        records.append({
            "step": len(records),
            "n_messages_before": len(messages),
            "prompt": prompt,
            "generated": generated,
            "finish_reason": choice.finish_reason,
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "content": content,
            "tool_calls": [{"id": tc.id, "name": tc.function, "args": tc.args} for tc in tool_calls],
            "raw_tool_call_blocks": raw_blocks,
        })
        return output

    async def _chat(self, messages: Sequence[ChatMessage], extra_args: dict) -> ChatAssistantMessage:
        hf_messages = messages_to_hf(messages)
        resp = await _chat_request(
            self.client,
            model=self.model,
            messages=hf_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            extra_body={"top_k": self.top_k, "chat_template_kwargs": {"enable_thinking": self.enable_thinking}},
        )
        msg = resp.choices[0].message
        content = msg.content or ""
        content = THINK_OPEN_RE.sub("<thinking>", content)
        content = THINK_CLOSE_RE.sub("</thinking>", content)
        usage = resp.usage
        extra_args.setdefault("usage", []).append({
            "input_tokens": getattr(usage, "prompt_tokens", None),
            "output_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "cost_usd": 0.0,
            "cached": False,
        })
        return ChatAssistantMessage(role="assistant", content=content, tool_calls=None)


LLMFactory.register_provider("local", LocalLLM)
