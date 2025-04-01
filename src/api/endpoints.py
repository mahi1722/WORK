import logging
from fastapi import FastAPI, HTTPException
from src.flow.graph import init_graph
from src.models.servicenow_api import APIResponse

app = FastAPI()
graph = None

@app.on_event("startup")
async def startup_event():
    global graph
    graph = await init_graph()

@app.get("/")
async def read_root():
    return {"message": "LangGraph Assistant is Running (Async)!"}

@app.post("/api/task")
async def execute_flow(task_data: APIResponse):
    try:
        task_response = task_data.model_dump()
        thread_id = "task_" + task_response["result"][0]["number"]
        output = await graph.ainvoke(
            {"task_response": task_response},
            config={"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
        )
        return output
    except Exception as e:
        logging.error(f"Error executing flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))