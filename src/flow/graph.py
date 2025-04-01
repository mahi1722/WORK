from langgraph.graph import StateGraph, START, END
from src.models.state import FlowState
from src.flow.supervisor import supervisor_node
from src.flow.agent import execute_action

async def ad_agent_node(state: FlowState) -> FlowState:
    state = await execute_action(state)
    return state

async def m365_agent_node(state: FlowState) -> FlowState:
    state = await execute_action(state)
    return state

async def init_graph():
    builder = StateGraph(FlowState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("ad_agent", ad_agent_node)
    builder.add_node("m365_agent", m365_agent_node)
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_step", "end"),
        {
            "ad_agent": "ad_agent",
            "m365_agent": "m365_agent",
            "end": END
        }
    )
    builder.add_edge("ad_agent", "supervisor")
    builder.add_edge("m365_agent", "supervisor")

    # Add checkpointing
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from src.utils.env import db_path
    conn = await aiosqlite.connect(db_path, check_same_thread=False)
    memory = AsyncSqliteSaver(conn)
    return builder.compile(checkpointer=memory)