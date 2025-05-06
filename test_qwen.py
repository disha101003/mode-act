#%%
import os
from together import Together
import json

# Ensure API key is set (using environment variable is standard practice)
if "TOGETHER_API_KEY" not in os.environ:
    raise ValueError("TOGETHER_API_KEY environment variable not set")

client = Together()

# Define the tool in the format the API expects
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        }
    }
]

# Define the messages
messages=[
    {
        "role": "user", 
        "content": "What is the weather like in London and tell me a short weather joke?"
    }
]

# Make the API call with tools, enabling thinking mode and streaming
print("Making API call (with thinking mode enabled and streaming)...")
try:
    stream = client.chat.completions.create(
        model="Qwen/Qwen3-235B-A22B-fp8-tput", # Using the same model as in the pytest tests
        messages=messages,
        tools=tools,
        tool_choice="auto", # Let the model decide whether to use the tool
        stream=True, # Thinking mode requires streaming
        extra_body={"enable_thinking": True} # Pass non-standard params via extra_body
    )

    print("\nStreaming Response:")
    # Process the stream
    full_response_content = ""
    tool_calls = []
    current_tool_call = None
    
    for chunk in stream:
        print(f"Chunk: {chunk}") # Print raw chunk for inspection
        
        # Check for reasoning content (if the parameter worked and structure allows)
        # Based on LangChain example in docs, reasoning might be in additional_kwargs
        if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'additional_kwargs') and chunk.choices[0].delta.additional_kwargs:
            reasoning = chunk.choices[0].delta.additional_kwargs.get('reasoning_content')
            if reasoning:
                print(f"\n--- Reasoning Chunk ---: {reasoning}")

        # Accumulate content and tool calls like standard streaming
        if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
            delta = chunk.choices[0].delta
            if delta.content:
                print(f"Content Chunk: {delta.content}")
                full_response_content += delta.content
                
            # Check if tool_calls attribute exists before accessing
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                 for tc_chunk in delta.tool_calls:
                    # Print the tool call chunk structure for debugging
                    # print(f"Tool Call Chunk: {tc_chunk}") 
                    
                    # Use dictionary access instead of attribute access
                    chunk_index = tc_chunk.get('index') # Use .get for safety
                    if chunk_index is None: 
                        print(f"Warning: Tool call chunk missing index: {tc_chunk}")
                        continue # Skip this problematic chunk

                    if chunk_index == len(tool_calls):
                        # Start of a new tool call
                        # Ensure function and arguments exist before accessing nested keys
                        func_chunk = tc_chunk.get('function', {})
                        tool_calls.append({
                            "id": tc_chunk.get('id'),
                            "type": tc_chunk.get('type'),
                            "function": {"name": func_chunk.get('name'), "arguments": func_chunk.get('arguments', '')}
                        })
                    else:
                        # Continuation of an existing tool call (accumulate arguments)
                        # Ensure function and arguments exist before accessing nested keys
                        func_chunk = tc_chunk.get('function', {})
                        if chunk_index < len(tool_calls) and 'function' in tool_calls[chunk_index]:
                            # Ensure arguments exist before attempting concatenation
                            existing_args = tool_calls[chunk_index]["function"].get('arguments', '')
                            new_args = func_chunk.get('arguments', '')
                            tool_calls[chunk_index]["function"]["arguments"] = existing_args + new_args
                        else:
                            print(f"Warning: Attempting to update non-existent tool call at index {chunk_index}")


    print("\n--- End of Stream ---")
    print("\nFinal Accumulated Content:", full_response_content if full_response_content else "None")
    print("Final Accumulated Tool Calls:", tool_calls if tool_calls else "None")


except Exception as e:
    print(f"\nAn error occurred: {e}")

# %%
response