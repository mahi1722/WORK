import json
import subprocess
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
import os
import sys

# Groq model initialization
GROQ_API_KEY = "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"
model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.2-3b-preview",
)

# Base directory for scripts
SCRIPTS_DIR = "scripts"

# Load config.yaml
with open("config.yaml", "r") as file:
    CONFIG = yaml.safe_load(file)

# Helper function to parse PowerShell JSON output
def parse_powershell_output(raw_output: str) -> Dict[str, Any]:
    """Parse JSON output from PowerShell scripts into a Python dictionary."""
    try:
        parsed = json.loads(raw_output.strip())
        return {
            "Status": parsed.get("Status", ""),
            "OutputMessage": parsed.get("OutputMessage", ""),
            "ErrorMessage": parsed.get("ErrorMessage", "")
        }
    except json.JSONDecodeError:
        return {
            "Status": "Error",
            "OutputMessage": "",
            "ErrorMessage": f"Failed to parse PowerShell output: {raw_output}"
        }

# Helper function to run PowerShell scripts
def run_powershell_script(script_name: str, argument: str) -> Dict[str, Any]:
    """Execute a PowerShell script from the scripts folder and return its parsed JSON output."""
    script_path = os.path.join(SCRIPTS_DIR, f"{script_name}.ps1")
    if not os.path.exists(script_path):
        return {
            "Status": "Error",
            "OutputMessage": "",
            "ErrorMessage": f"Script {script_path} not found in {SCRIPTS_DIR} folder."
        }

    try:
        result = subprocess.run(
            ["powershell", "-File", script_path, argument],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        if not output:
            return {
                "Status": "Success",
                "OutputMessage": f"{script_name} executed successfully with no output.",
                "ErrorMessage": ""
            }
        return parse_powershell_output(output)
    except subprocess.CalledProcessError as e:
        return {
            "Status": "Error",
            "OutputMessage": "",
            "ErrorMessage": f"Error executing {script_name}.ps1: {e.stderr}"
        }


# Tool functions with docstrings
def parse_variables(query: str) -> Dict[str, Any]:
    """Parse variables from the input query for further processing.
    
    Args:
        query (str): The input query containing variables to parse
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("parse_varaibles", query)

def check_ad_group_existence(group_name: str) -> Dict[str, Any]:
    """Check if an Active Directory security group exists.
    
    Args:
        group_name (str): Name of the AD security group to check
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("Check_Ad_Group_Existence", group_name)

def check_owner_existence(owner_name: str) -> Dict[str, Any]:
    """Verify if the specified owner exists in Active Directory.
    
    Args:
        owner_name (str): Name of the owner to check
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("Check_Owner_Existance", owner_name)

def create_ad_group(group_name: str) -> Dict[str, Any]:
    """Create a new Active Directory security group.
    
    Args:
        group_name (str): Name of the group to create
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("Create_Ad_Group", group_name)

def check_m365_license(user_id: str) -> Dict[str, Any]:
    """Check Microsoft 365 license assignments for a user.
    
    Args:
        user_id (str): User ID to check licenses for
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("check_m365_license", user_id)

def sam_name_validation(query: str) -> Dict[str, Any]:
    """Validate SAM account name format.
    
    Args:
        query (str): SAM account name to validate
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("SAMNameValidation", query)

def display_name_validation(query: str) -> Dict[str, Any]:
    """Validate display name format.
    
    Args:
        query (str): Display name to validate
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("DisplayNameValidation", query)

def check_user_existence_output_samaccount(query: str) -> Dict[str, Any]:
    """Check if user exists and return their SAM account name.
    
    Args:
        query (str): User information to check
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("Check_User_existence_output_samaccount", query)

def add_user_to_security_group(query: str) -> Dict[str, Any]:
    """Add one or more users to an Active Directory security group.
    
    Args:
        query (str): User and group information
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("Add_user_to_security_group(single_or_multiple)", query)

def create_dl(query: str) -> Dict[str, Any]:
    """Create a Microsoft 365 distribution list.
    
    Args:
        query (str): Distribution list information
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("create_dl", query)

def modify_dl(query: str) -> Dict[str, Any]:
    """Modify an existing Microsoft 365 distribution list.
    
    Args:
        query (str): Distribution list modification details
        
    Returns:
        Dict[str, Any]: Status and message information
    """
    return run_powershell_script("modify_dl", query)



# Dynamic tool lookup
def get_tool_function(tool_name: str) -> Callable[[str], Dict[str, Any]]:
    """Dynamically retrieve a tool function by name."""
    tool_functions = {
        "parse_varaibles": parse_variables,
        "SAMNameValidation": sam_name_validation,
        "DisplayNameValidation": display_name_validation,
        "Check_Ad_Group_Existence": check_ad_group_existence,
        "Check_Owner_Existance": check_owner_existence,
        "Create_Ad_Group": create_ad_group,
        "Check_User_existence_output_samaccount": check_user_existence_output_samaccount,
        "Add_user_to_security_group(single_or_multiple)": add_user_to_security_group,
        "create_dl": create_dl,
        "modify_dl": modify_dl,
        "check_m365_license": check_m365_license
    }
    return tool_functions.get(tool_name, lambda x: {
        "Status": "Error",
        "OutputMessage": "",
        "ErrorMessage": f"Unknown tool: {tool_name}"
    })

# Dynamic prompts
def create_ad_agent_prompt() -> str:
    ad_config = CONFIG["Ad_agent"]
    tasks = "\n".join([f"- {key}: {', '.join(value)}" for key, value in ad_config.items()])
    return (
        "You are an Active Directory (AD) expert. Based on the user's query, execute the appropriate tools in order. "
        "Available tasks and their tool sequences from config.yaml:\n"
        f"{tasks}\n"
        "Use the tools as needed to process the query."
    )

def create_m365_agent_prompt() -> str:
    m365_config = CONFIG["m365_agent"]
    tasks = "\n".join([f"- {key}: {', '.join(value)}" for key, value in m365_config.items()])
    return (
        "You are a Microsoft 365 (M365) expert. Based on the user's query, execute the appropriate tools in order. "
        "Available tasks and their tool sequences from config.yaml:\n"
        f"{tasks}\n"
        "Use the tools as needed to process the query."
    )

def create_supervisor_prompt() -> str:
    workflows = CONFIG.get("workflows", {})
    workflow_info = "\n".join([
        f"- {name}: {', '.join(details['tools'])}" 
        for name, details in workflows.items()
    ])
    return (
        "You are a team supervisor managing a workflow system. "
        "Based on the user's query, determine the appropriate workflow and tools to execute.\n"
        "Available workflows and their tool sequences:\n"
        f"{workflow_info}\n"
        "Return a JSON object with 'workflow' (workflow name from config) and 'tools' (array of tool names in execution order).\n"
        "You can combine tools from different workflows if needed.\n"
        "If the query doesn't match any workflow, return {'workflow': 'none', 'tools': []}."
    )

# Create agents
ad_tools = [get_tool_function(tool) for task in CONFIG["Ad_agent"].values() for tool in task]
ad_agent = create_react_agent(
    model=model,
    tools=ad_tools,
    name="ad_expert",
    prompt=create_ad_agent_prompt()
)

m365_tools = [get_tool_function(tool) for task in CONFIG["m365_agent"].values() for tool in task]
m365_agent = create_react_agent(
    model=model,
    tools=m365_tools,
    name="m365_expert",
    prompt=create_m365_agent_prompt()
)

# Create supervisor
workflow = create_supervisor(
    [ad_agent, m365_agent],
    model=model,
    prompt=create_supervisor_prompt()
)

# Define the state type for the workflow
@dataclass
class GraphState:
    ticket_number: str = ""
    short_description: str = ""
    next_step: str = ""
    process_complete: bool = False
    additional_variables: Dict[str, Any] = field(default_factory=dict)
    tool_logs: List[Dict[str, Any]] = field(default_factory=list)

# Supervisor Node
def supervisor_node(state: GraphState) -> Dict[str, Any]:
    if state.process_complete:
        return {"next_step": "end"}

    additional_variables = state.additional_variables.copy()
    additional_variables["ticket_info"] = f"Ticket {state.ticket_number}: {state.short_description}"

    # Use the supervisor agent to determine the workflow and tools
    supervisor_response = ad_agent.invoke({"input": state.short_description})  # Correct the agent used here
    try:
        if isinstance(supervisor_response, str):
            decision = json.loads(supervisor_response)
        else:
            decision = supervisor_response
        
        workflow_name = decision.get("workflow", "none")
        tools = decision.get("tools", [])
    except (json.JSONDecodeError, AttributeError):
        return {
            "next_step": "end",
            "process_complete": True,
            "additional_variables": additional_variables
        }

    if workflow_name == "none" or not tools:
        return {
            "next_step": "end",
            "process_complete": True,
            "additional_variables": additional_variables
        }

    additional_variables["tool_order"] = tools
    additional_variables["current_tool_idx"] = 0

    # Determine next agent based on the first tool
    first_tool = tools[0]
    workflow_config = CONFIG.get("workflows", {}).get(workflow_name, {})
    next_agent = "ad_agent" if workflow_config.get("agent") == "ad_agent" else "m365_agent"

    return {
        "next_step": next_agent,
        "additional_variables": additional_variables,
        "process_complete": False
    }

# Generic Agent Node (used for both AD and M365)
def agent_node(state: GraphState) -> Dict[str, Any]:
    additional_variables = state.additional_variables.copy()
    tool_logs = state.tool_logs.copy()

    tool_order = additional_variables.get("tool_order", [])
    current_tool_idx = additional_variables.get("current_tool_idx", 0)

    if current_tool_idx >= len(tool_order):
        return {
            "process_complete": True,
            "next_step": "supervisor",
            "additional_variables": additional_variables,
            "tool_logs": tool_logs
        }

    current_tool = tool_order[current_tool_idx]
    tool_func = get_tool_function(current_tool)
    result = tool_func(state.short_description)

    tool_log = {"tool_name": current_tool, "result": result}
    tool_logs.append(tool_log)

    additional_variables["current_tool_idx"] = current_tool_idx + 1

    return {
        "next_step": "supervisor",
        "process_complete": False,
        "additional_variables": additional_variables,
        "tool_logs": tool_logs
    }

# Build graph
builder = StateGraph(GraphState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("ad_agent", agent_node)  # Use generic agent_node
builder.add_node("m365_agent", agent_node)  # Use generic agent_node
builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    lambda state: state.next_step,
    {
        "ad_agent": "ad_agent",
        "m365_agent": "m365_agent",
        "end": END
    }
)
builder.add_edge("ad_agent", "supervisor")
builder.add_edge("m365_agent", "supervisor")
graph = builder.compile()

# Format tool logs for final output
def format_tool_logs(tool_logs: List[Dict[str, Any]]) -> str:
    if not tool_logs:
        return "No tools were executed."
    output = []
    for i, log in enumerate(tool_logs, start=1):
        result = log['result']
        status = result['Status']
        message = result['OutputMessage'] if result['OutputMessage'] else result['ErrorMessage']
        output.append(f"Step {i}: {log['tool_name']} - Status: {status}, Message: {message}")
    return "\n".join(output)

# Run test
if __name__ == "__main__":
    # Test case 1: Active Directory Security Group Creation
    initial_input_ad = {
        "ticket_number": "12345",
        "short_description": "Need to create an Active Directory security group for the sales team",
        "next_step": "supervisor",
        "additional_variables": {}
    }

    result_ad = graph.invoke(initial_input_ad)
    tool_logs_ad = result_ad.get("tool_logs", [])
    overall_response_ad = format_tool_logs(tool_logs_ad)
    print("Overall Response for Active Directory Task:\n", overall_response_ad)

    # Test case 2: Microsoft 365 Create DL
    initial_input_m365 = {
        "ticket_number": "67890",
        "short_description": "Create Microsoft 365 distribution list for marketing",
        "next_step": "supervisor",
        "additional_variables": {}
    }

    result_m365 = graph.invoke(initial_input_m365)
    tool_logs_m365 = result_m365.get("tool_logs", [])
    overall_response_m365 = format_tool_logs(tool_logs_m365)
    print("\nOverall Response for Microsoft 365 Task:\n", overall_response_m365)

    # Test case 3: Hybrid workflow using both AD and M365 tools
    initial_input_hybrid = {
        "ticket_number": "13579",
        "short_description": "Create new user account with AD profile and M365 license",
        "next_step": "supervisor",
        "additional_variables": {}
    }

    result_hybrid = graph.invoke(initial_input_hybrid)
    tool_logs_hybrid = result_hybrid.get("tool_logs", [])
    overall_response_hybrid = format_tool_logs(tool_logs_hybrid)
    print("\nOverall Response for Hybrid Task:\n", overall_response_hybrid)