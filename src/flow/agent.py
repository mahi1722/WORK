"""
Agent module for ServiceNow automation workflow execution.
Handles workflow orchestration and tool execution.
"""

import json
import yaml
from typing import Dict, Any
from langchain_groq import ChatGroq
from src.services.script_executor import run_script
from src.utils.config import load_config
from src.models.state import FlowState

class AgentError(Exception):
    """Custom exception for agent-related errors"""
    pass

# Initialize services
model = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")
config = load_config("config/workflows.yaml")

def get_agent_prompt(state: FlowState) -> str:
    """
    Generate a prompt for the workflow agent.
    
    Args:
        state: Current workflow state containing ticket and action information
        
    Returns:
        str: Formatted prompt for the agent
    """
    try:
        ticket_desc = state['task_response']['result'][0]['short_description']
        
        return f"""
        You are an agent executing tools for a ServiceNow ticket.

        ### Current State:
        - Flow: {state['flow_name']}
        - Description: {ticket_desc}
        - Actions: {state['actions_list']}
        - Current: {state['current_action']}
        - Index: {state['action_index']}
        - Variables: {state['additional_variables']}
        - Log: {state['execution_log']}

        ### Config:
        ```yaml
        {yaml.dump(config, default_flow_style=False)}
        ```

        ### Instructions:
        1. Execute the current action per the config.
        2. Adjust actions_list based on results.
        3. Return JSON with:
           - next_action: Next tool or "" if done
           - updated_actions_list: Revised tool list
           - additional_variables: Updated variables
           - worknote_content: Work note message

        ### Example Response:
        ```json
        {{
          "next_action": "create_ad_user",
          "updated_actions_list": ["create_ad_user", "update_ticket"],
          "additional_variables": {{"user_exists": false}},
          "worknote_content": "User does not exist."
        }}
        ```
        """
    except KeyError as e:
        raise AgentError(f"Missing required state field: {e}")

async def execute_action(state: FlowState) -> FlowState:
    """
    Execute the current workflow action and update state.
    
    Args:
        state: Current workflow state
        
    Returns:
        FlowState: Updated workflow state
        
    Raises:
        AgentError: If there's an error during execution
    """
    try:
        # Get agent decision
        prompt = get_agent_prompt(state)
        response = model.invoke(prompt)
        result = json.loads(response.content)

        # Execute tool
        tool_info = config["tools"][state["current_action"]]
        script_result = await run_script(
            script=tool_info["script"],
            variables=state["additional_variables"],
            ticket_data=state["task_response"]
        )

        # Handle execution results
        if script_result["Status"] == "Error":
            state.update({
                "error_occurred": True,
                "worknote_content": f"Error in {state['current_action']}: {script_result['ErrorMessage']}",
                "reassignment_group": "IT Support",
                "execution_log": state["execution_log"] + [{
                    "action": state["current_action"],
                    "result": script_result,
                    "error": True
                }]
            })
        else:
            # Update state with successful execution
            state.update({
                "worknote_content": result["worknote_content"],
                "actions_list": result["updated_actions_list"],
                "current_action": result["next_action"],
                "next_action": bool(result["next_action"]),
                "additional_variables": {**state["additional_variables"], **result["additional_variables"]},
                "action_index": state["actions_list"].index(result["next_action"]) if result["next_action"] else -1,
                "execution_log": state["execution_log"] + [{
                    "action": state["current_action"],
                    "result": script_result
                }]
            })

    except (json.JSONDecodeError, KeyError) as e:
        state.update({
            "error_occurred": True,
            "error_message": f"Agent execution error: {str(e)}",
            "reassignment_group": "IT Support"
        })
        
    return state