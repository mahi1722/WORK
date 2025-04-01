"""
Supervisor module for ServiceNow ticket automation workflow selection.
Handles ticket analysis and workflow orchestration.
"""

import json
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from src.utils.config import load_config
from src.models.state import FlowState, TicketState
from src.services.servicenow import update_work_notes, update_ticket_state

# Initialize services
model = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")
config = load_config("config/workflows.yaml")

def get_supervisor_prompt(task_response: Dict[str, Any]) -> str:
    """
    Generate a prompt for the supervisor based on ticket information.
    
    Args:
        task_response: Dictionary containing ticket information
        
    Returns:
        str: Formatted prompt for the workflow supervisor
        
    Raises:
        ValueError: If required ticket fields are missing
    """
    try:
        ticket_description = task_response["result"][0]["short_description"]
        ticket_number = task_response["result"][0]["number"]
        workflows = "\n".join([
            f"- {name}: {details['description']}" 
            for name, details in config['workflows'].items()
        ])
        
        return f"""
        You are a supervisor for ServiceNow ticket automation.
        Analyze the ticket and select the best workflow.

        ### Ticket Info:
        - Number: {ticket_number}
        - Description: {ticket_description}

        ### Workflows:
        {workflows}

        ### Instructions:
        1. Match the description to a workflow.
        2. Extract variables (e.g., username).
        3. Return JSON with:
           - `flow_name`: Workflow name.
           - `actions_list`: Tool order.
           - `additional_variables`: Extracted variables.

        ### Example:
        Ticket: "Create AD user jdoe"
        ```json
        {{
          "flow_name": "ADUserCreation",
          "actions_list": ["parse_variables", "check_ad_user_existence", "create_ad_user", "update_ticket"],
          "additional_variables": {{"username": "jdoe"}}
        }}
        """
    except (KeyError, IndexError) as e:
        raise ValueError(f"Invalid ticket response format: {e}")

async def supervisor_node(state: FlowState) -> FlowState:
    """
    Process the ticket and determine next workflow steps.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
        
    Raises:
        json.JSONDecodeError: If model response cannot be parsed
    """
    # Handle work notes update if needed
    if state["worknote_content"]:
        state = await update_work_notes(state)

    # Handle error conditions
    if state["error_occurred"]:
        if state["reassignment_group"]:
            state["task_response"]["result"][0]["assignment_group"] = state["reassignment_group"]
        state["next_step"] = "to_end"
        return state

    # Handle completion
    if not state["next_action"]:
        state = await update_ticket_state(state, TicketState.RESOLVED)
        state["execution_log"].append({
            "action": "supervisor",
            "description": "Process complete."
        })
        state["next_step"] = "to_end"
        return state

    # Initialize workflow if needed
    if not state["flow_name"]:
        try:
            prompt = get_supervisor_prompt(state["task_response"])
            response = model.invoke(prompt)
            result = json.loads(response.content)
            
            # Update state with workflow information
            state.update({
                "flow_name": result["flow_name"],
                "actions_list": result["actions_list"],
                "current_action": result["actions_list"][0],
                "action_index": 0,
                "additional_variables": result["additional_variables"]
            })
            
            # Determine next step based on workflow
            state["next_step"] = {
                "ADUserCreation": "ad_agent",
                "M365LicenseCheck": "m365_agent"
            }.get(state["flow_name"], "to_end")
            
        except json.JSONDecodeError as e:
            state["error_occurred"] = True
            state["error_message"] = f"Failed to parse model response: {str(e)}"
            state["next_step"] = "to_end"
            
    return state