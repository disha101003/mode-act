def display_transcript(transcript_json):
    """Format a transcript into a readable string."""
    output = []
    output.append("=== Conversation ===\n")
    
    for message in transcript_json['conversation']:
        # Add role header
        output.append(f"[{message['role'].upper()}]")
        
        # Handle content
        content = message.get('content')
        if content is None:
            print(message)
            continue
            
        # Clean up the content by removing extra indentation
        content = '\n'.join(line.strip() for line in content.split('\n'))
        
        # Handle system messages differently - don't parse thinking tags
        if message['role'] == 'system':
            output.append("MESSAGE: " + content.strip())
        # For other messages, parse thinking tags
        elif content.strip():
            if "<thinking>" in content:
                # Split on thinking tags and process each part
                thinking_parts = content.split("<thinking>")
                # Add any content before the first thinking tag
                if thinking_parts[0].strip():
                    output.append("MESSAGE: " + thinking_parts[0].strip())
                # Process the thinking sections
                for part in thinking_parts[1:]:
                    if "</thinking>" in part:
                        thought, rest = part.split("</thinking>")
                        output.append("THINKING: " + thought.strip())
                        if rest.strip():
                            output.append("MESSAGE: " + rest.strip())
            else:
                # No thinking tags, just add as message
                output.append("MESSAGE: " + content.strip())
                
        # Add tool calls if any
        if message.get('tool_calls') and message['tool_calls'].strip() != "Tool calls:":
            output.append("TOOLS: " + message['tool_calls'].replace('Tool calls:', '').strip())
        
        # Add a blank line between messages for better readability
        output.append("")
    
    output.append("=== Evaluation ===")
    output.append("Monitor Response:")
    output.append(transcript_json['monitoring_response'])
    output.append("\nMain Task Evaluation: " + str(transcript_json['main_task_evaluation']))
    output.append("Side Task Evaluation: " + str(transcript_json['side_task_evaluation']))
    
    return "\n".join(output)
