#!/usr/bin/env python
"""
Formatting utilities for the Estate Planning Agent CLI interface.
"""

from typing import Dict, Any, List


class Colors:
    """ANSI color codes for terminal output formatting."""
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def format_value(value: Any, indent_level: int = 0, key: str = None) -> str:
    """
    Format a value for readable console output.
    
    Args:
        value: The value to format
        indent_level: Current indentation level
        key: Optional key name for context-aware formatting
        
    Returns:
        Formatted string representation
    """
    indent = "  " * indent_level
    
    if isinstance(value, dict):
        if not value:
            return f"{indent}(empty)"
        
        # Special case for content with text field (common in API responses)
        if "text" in value and isinstance(value["text"], str):
            return f"{indent}{value['text']}"
            
        lines = []
        # Sort keys for more logical display
        for k in sorted(value.keys()):
            v = value[k]
            lines.append(f"{indent}{Colors.UNDERLINE}{k}:{Colors.END}")
            lines.append(format_value(v, indent_level + 1, k))
        return "\n".join(lines)
    
    elif isinstance(value, list):
        if not value:
            return f"{indent}(empty list)"
        
        # Special case for short simple lists
        if len(value) <= 5 and all(isinstance(item, (str, int, float, bool)) for item in value):
            items_str = ", ".join(str(item) for item in value)
            return f"{indent}[{items_str}]"
            
        lines = []
        for i, item in enumerate(value, 1):
            if isinstance(item, dict) and "text" in item:
                # Special handling for text content
                lines.append(f"{indent}{Colors.BOLD}Item {i}:{Colors.END}")
                lines.append(f"{indent}  {item['text']}")
            else:
                lines.append(f"{indent}{Colors.BOLD}Item {i}:{Colors.END}")
                lines.append(format_value(item, indent_level + 1))
        return "\n".join(lines)
    
    elif isinstance(value, str):
        # Handle JSON string
        if (value.startswith('{') and value.endswith('}')) or (value.startswith('[') and value.endswith(']')):
            try:
                import json
                parsed = json.loads(value)
                formatted = json.dumps(parsed, indent=2)
                lines = formatted.split('\n')
                return "\n".join(f"{indent}{line}" for line in lines)
            except:
                pass  # Not valid JSON, fall through to normal string handling
                
        # Handle multi-line strings
        if '\n' in value:
            lines = value.split('\n')
            return "\n".join(f"{indent}{line}" for line in lines)
            
        # Format based on key context
        if key and key.endswith(("_id", "Id")):
            return f"{indent}{Colors.BLUE}{value}{Colors.END}"
        elif key and key.endswith(("_date", "Date", "timestamp", "Timestamp")):
            return f"{indent}{Colors.YELLOW}{value}{Colors.END}"
        else:
            return f"{indent}{value}"
    
    elif isinstance(value, bool):
        # Color code boolean values
        color = Colors.GREEN if value else Colors.RED
        return f"{indent}{color}{value}{Colors.END}"
        
    elif value is None:
        return f"{indent}{Colors.RED}None{Colors.END}"
        
    else:
        return f"{indent}{value}"


def display_response(response: Dict[str, Any]) -> None:
    """
    Display the agent's response with formatting.
    
    Args:
        response: The parsed JSON response from the agent
    """
    import textwrap
    wrapper = textwrap.TextWrapper(width=100, break_long_words=False, replace_whitespace=False)
    
    # Display the main response message
    if "result" in response:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🤖 AGENT RESPONSE{Colors.END}")
        print(f"{Colors.GREEN}{'=' * 50}{Colors.END}")
        
        # If result is a dictionary or has nested content (like content array in OpenAI format)
        if isinstance(response["result"], dict):
            # Handle OpenAI format which might be nested
            if "content" in response["result"]:
                if isinstance(response["result"]["content"], list):
                    for item in response["result"]["content"]:
                        if isinstance(item, dict) and "text" in item:
                            # Wrap text for better display
                            wrapped_text = wrapper.fill(item['text'])
                            print(f"{Colors.GREEN}{wrapped_text}{Colors.END}")
                        else:
                            print(f"{Colors.GREEN}{item}{Colors.END}")
                else:
                    wrapped_text = wrapper.fill(str(response['result']['content']))
                    print(f"{Colors.GREEN}{wrapped_text}{Colors.END}")
            else:
                # Pretty print the dictionary
                import json
                formatted_json = json.dumps(response["result"], indent=2)
                print(f"{formatted_json}")
        else:
            # Simple string output - wrap for better display
            wrapped_text = wrapper.fill(str(response['result']))
            print(f"{Colors.GREEN}{wrapped_text}{Colors.END}")
    
    # Display other fields with headers, but handle remote agent fields specially
    excluded_fields = ["result", "error_details", "raw_response"]
    other_fields = {k: v for k, v in response.items() 
                   if k not in excluded_fields and not k.startswith("_")}
    
    # Special handling for remote agent metadata
    if "metadata" in response:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}📋 METADATA{Colors.END}")
        print(f"{Colors.YELLOW}{'=' * 11}{Colors.END}")
        formatted_metadata = format_value(response["metadata"], key="metadata")
        print(formatted_metadata)
    
    # Special handling for tools_used
    if "tools_used" in response:
        tools = response.get("tools_used", [])
        if tools:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}🔧 TOOLS USED{Colors.END}")
            print(f"{Colors.YELLOW}{'=' * 13}{Colors.END}")
            for i, tool in enumerate(tools, 1):
                print(f"{Colors.YELLOW}{i}. {tool}{Colors.END}")
    
    # Special handling for action_required
    if "action_required" in response:
        action_required = response.get("action_required", False)
        print(f"\n{Colors.YELLOW}{Colors.BOLD}❓ ACTION REQUIRED: {Colors.END}", end="")
        if action_required:
            print(f"{Colors.GREEN}Yes{Colors.END}")
        else:
            print(f"{Colors.RED}No{Colors.END}")
    
    # Handle remaining fields
    for key, value in other_fields.items():
        if key in ["metadata", "tools_used", "action_required"]:
            continue  # Already handled specially
            
        if key == "error" and value is None:
            continue
            
        # Create a readable header for each field
        header = key.replace('_', ' ').title()
        print(f"\n{Colors.YELLOW}{Colors.BOLD}📋 {header.upper()}{Colors.END}")
        print(f"{Colors.YELLOW}{'=' * (len(header) + 4)}{Colors.END}")
        
        formatted_value = format_value(value, key=key)
        print(formatted_value)
    
    print()  # Add extra line break for better spacing


def print_header() -> None:
    """Print a welcome header for the test interface."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("🔍 ESTATE PLANNING AGENT - LOCAL TESTING INTERFACE")
    print("=" * 70)
    print(f"""
This interface lets you interactively test your local estate planning agent.

{Colors.BOLD}Available Commands:{Colors.END}{Colors.BLUE}
- Type your questions or responses and press Enter
- Type {Colors.YELLOW}'clear'{Colors.BLUE} to start a new conversation
- Type {Colors.YELLOW}'state'{Colors.BLUE} to see the conversation history
- Type {Colors.YELLOW}'exit'{Colors.BLUE} or {Colors.YELLOW}'quit'{Colors.BLUE} to end the session
""")


def display_conversation_history(history: List[tuple]) -> None:
    """
    Display the conversation history.
    
    Args:
        history: List of (role, text) tuples representing the conversation
    """
    print(f"\n{Colors.YELLOW}Conversation History:{Colors.END}")
    for i, (role, text) in enumerate(history):
        prefix = "🤖 Agent" if role == "agent" else "👤 You"
        print(f"{i+1}. {Colors.BOLD}{prefix}:{Colors.END} {text}")